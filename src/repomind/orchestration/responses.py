from data.constants import AgentEventType, AgentStatus, GuardrailStatus
from data.models import AgentEvent, AgentState, LLMDecision, LLMResponse

from ..guardrails import check_completion
from ..state import next_sequence, save_state


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
            type=AgentEventType.INVESTIGATION_CONTINUED,
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
            type=AgentEventType.INVESTIGATION_CANNOT_COMPLETE,
            step=state.step,
            sequence=next_sequence(state),
            reason=decision.reason,
            required_action=None,
        )
    )

    save_state(state)


def handle_final_answer(
    state: AgentState,
    answer: str,
) -> None:
    """
    Validate a separately generated final answer.

    The answer is ordinary model-generated text. The application
    decides whether it satisfies the completion guardrails.
    """

    answer = answer.strip()

    if not answer:
        print("\nModel generated an empty final answer. Continuing the investigation.")

        state.events.append(
            AgentEvent(
                type=AgentEventType.INVESTIGATION_CONTINUED,
                step=state.step,
                sequence=next_sequence(state),
                reason="The final-answer generation returned empty content.",
                required_action="Generate a non-empty final answer.",
            )
        )

        save_state(state)
        return

    guardrail = check_completion(
        state,
        answer,
    )

    if guardrail.status == GuardrailStatus.BLOCKED:
        print("\nGuardrail blocked completion:")
        print(f"Reason: {guardrail.reason}")
        print(f"Required action: {guardrail.required_action}")

        state.events.append(
            AgentEvent(
                type=AgentEventType.GUARDRAIL_BLOCKED,
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

    state.status = AgentStatus.COMPLETED

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
            type=AgentEventType.GENERATION_TRUNCATED,
            phase=llm_response.phase,
            step=state.step,
            sequence=next_sequence(state),
            reason="The model generation stopped because it reached the configured output limit.",
            required_action=(
                "Continue the previous response from where it stopped. Do not restart the answer."
            ),
        )
    )

    save_state(state)
