from ..guardrails import check_completion
from ..models import AgentEvent, AgentState, LLMDecision, LLMResponse
from ..state import next_sequence, save_state
from .tool_calls import handle_tool_calls


def handle_missing_decision(
    state: AgentState,
) -> None:
    """
    Handle a response that contains neither tool calls nor a decision.

    Such a response must never be treated as a final answer.
    """

    print(
        "\nModel returned no tool calls and no structured decision. Continuing the investigation."
    )

    state.events.append(
        AgentEvent(
            type="investigation_continued",
            step=state.step,
            sequence=next_sequence(state),
            reason="The model response did not contain a structured investigation decision.",
            required_action=(
                "Return a valid structured investigation decision or request a repository tool."
            ),
        )
    )

    save_state(state)


def handle_cannot_complete(
    state: AgentState,
    decision: LLMDecision,
) -> None:
    """
    Record that the model could not complete the investigation.

    This does not mark the agent as completed. The application must
    decide later how this condition should be exposed or retried.
    """

    print("\nModel reported that it cannot complete the investigation.")
    print(f"Reason: {decision.reason}")

    state.events.append(
        AgentEvent(
            type="investigation_cannot_complete",
            step=state.step,
            sequence=next_sequence(state),
            reason=decision.reason,
            required_action=None,
        )
    )

    save_state(state)


def handle_final_answer_proposal(
    state: AgentState,
    decision: LLMDecision,
) -> None:
    """
    Validate a model-proposed final answer.

    The model may propose completion, but the application decides
    whether the answer satisfies the completion guardrails.
    """

    answer = (decision.answer or "").strip()

    if not answer:
        print(
            "\nModel proposed a final answer, but the answer content "
            "was empty. Continuing the investigation."
        )

        state.events.append(
            AgentEvent(
                type="investigation_continued",
                step=state.step,
                sequence=next_sequence(state),
                reason=("The model proposed a final answer without providing answer content."),
                required_action=("Return a non-empty answer or continue investigating."),
            )
        )

        save_state(state)
        return

    guardrail = check_completion(
        state,
        answer,
    )

    if guardrail.status == "blocked":
        print("\nGuardrail blocked completion:")
        print(f"Reason: {guardrail.reason}")
        print(f"Required action: {guardrail.required_action}")

        state.events.append(
            AgentEvent(
                type="guardrail_blocked",
                step=state.step,
                sequence=next_sequence(state),
                reason=guardrail.reason,
                required_action=guardrail.required_action,
            )
        )

        save_state(state)
        return

    print("\nFinal answer:")
    print(answer)

    state.status = "completed"

    save_state(state)


def handle_generation_truncated(
    state: AgentState,
    llm_response: LLMResponse,
) -> None:
    """
    Record a truncated model generation.

    A length finish reason never represents successful completion.
    """

    content = llm_response.content

    if content.strip():
        print("\nModel generation reached the output limit. Recording incomplete generation.")
    else:
        print("\nModel generation reached the output limit without producing answer content.")

    state.events.append(
        AgentEvent(
            type="generation_truncated",
            step=state.step,
            sequence=next_sequence(state),
            reason=("The model generation stopped because it reached the configured output limit."),
            required_action=(
                "Continue the previous response from where it stopped. Do not restart the answer."
            ),
        )
    )

    save_state(state)


def handle_no_tool_response(
    state: AgentState,
    llm_response: LLMResponse,
) -> None:
    """
    Handle an LLM response that contains no tool calls.

    A no-tool response is not automatically final.

    A structured decision is handled only when one was explicitly
    requested. Otherwise, the response is treated as incomplete
    and must not become a final answer.
    """

    if llm_response.finish_reason == "length":
        handle_generation_truncated(
            state,
            llm_response,
        )
        return

    decision = llm_response.decision

    if decision is None:
        handle_missing_decision(state)
        return

    match decision.decision:
        case "cannot_complete":
            handle_cannot_complete(
                state,
                decision,
            )

        case "propose_final_answer":
            handle_final_answer_proposal(
                state,
                decision,
            )


def handle_llm_response(
    state: AgentState,
    llm_response,
) -> None:
    """
    Route the LLM response to the appropriate handler.

    This function decides which response category needs handling,
    but the individual handlers own the actual behavior.
    """

    if llm_response.tool_calls:
        handle_tool_calls(
            state,
            llm_response.tool_calls,
        )
        return

    handle_no_tool_response(
        state,
        llm_response,
    )
