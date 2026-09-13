from .answers.reconstruction import collect_answer_fragments
from .context.builder import (
    build_context,
)
from .display import print_tool_result
from .evidence.store import resolve_evidence_source
from .executor import execute_tool
from .guardrails import check_completion
from .llm import chat
from .models import AgentEvent, AgentState, PendingToolCall, ToolExecutionResult
from .registry import tool_registry, tools
from .state import create_message, next_sequence, save_state
from .tool_messages import tool_result_message
from .tool_results import process_tool_result

# --------------------------------------------------
# One agent step
# --------------------------------------------------


def run_agent_step(state: AgentState) -> None:

    state.step += 1

    print(f"\n--- Agent step {state.step} ---")

    context = build_context(state)

    print(f"\nContext prepared: {len(context)} messages")

    llm_response = chat(messages=context, tools=tools)

    done_reason = llm_response.finish_reason
    tool_calls = llm_response.tool_calls

    # Reconstruct the assistant message payload that will be
    # persisted in AgentState and sent back to Ollama later.
    assistant_message: dict[str, object] = {
        "role": "assistant",
        "content": llm_response.content,
    }

    # Ollama expects tool calls in its assistant message format.
    # Convert our internal LLMToolCall models back into that format.
    if tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                },
            }
            for tool_call in tool_calls
        ]
        print(f"Tool calls: {len(tool_calls)}")
    else:
        print(f"Content length: {len(llm_response.content)} characters")

    print("\nAssistant response received:")
    print(f"Done reason: {done_reason}")

    # Persist assistant message in conversation

    state.messages.append(
        create_message(
            state,
            assistant_message,
        )
    )

    # --------------------------------------------------
    # Final answer / incomplete model response
    # --------------------------------------------------

    if not tool_calls:
        content = llm_response.content

        # Ollama stopped generation because the model reached
        # the configured output limit. Non-empty content does
        # not necessarily represent a completed answer.
        if done_reason == "length":
            if content.strip():
                print(
                    "\nModel generation reached the output limit. "
                    "Recording incomplete generation and continuing the agent loop."
                )

                state.events.append(
                    AgentEvent(
                        type="generation_truncated",
                        step=state.step,
                        sequence=next_sequence(state),
                        reason=(
                            "The model generation stopped because it reached "
                            "the configured output limit."
                        ),
                        required_action=(
                            "Continue the previous response from where it stopped. "
                            "Do not restart the answer."
                        ),
                    )
                )

            else:
                print(
                    "\nModel generation reached the output limit without producing answer content."
                )

            save_state(state)

            return

        # An empty response without tool calls is not a final answer.
        # The model produced neither an action nor usable answer content.
        if not content.strip():
            print(
                "\nModel returned no tool calls and no answer content. Continuing the agent loop."
            )

            save_state(state)

            return

        # Reconstruct the complete answer artifact when this generation
        # finishes normally after one or more truncated generations.
        answer = collect_answer_fragments(state)

        # Only actual answer content is evaluated as a completion attempt.
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

        return

    # --------------------------------------------------
    # Tool calls
    # --------------------------------------------------

    for tool_call in tool_calls:
        tool_name = tool_call.name

        tool_arguments = tool_call.arguments

        print(f"\nTool requested: {tool_name}")

        print("Arguments:", tool_arguments)

        execution = execute_tool(tool_name, tool_arguments)

        tool_definition = tool_registry[tool_name]

        process_tool_result(state, tool_definition, tool_arguments, execution)

        # --------------------------------------------------
        # Approval required
        # --------------------------------------------------

        if execution.status == "approval_required":
            state.pending_tool_call = PendingToolCall(
                tool_call_id=tool_call.id,
                tool_name=tool_name,
                arguments=tool_arguments,
            )

            state.status = "waiting_for_approval"

            save_state(state)

            print("\nAgent paused waiting for approval.")

            return

        # --------------------------------------------------
        # Tool result
        # --------------------------------------------------

        print_tool_result(execution)

        source = None

        if execution.status == "success" and tool_definition.evidence is not None:
            source = resolve_evidence_source(
                tool_definition.evidence,
                tool_arguments,
            )

        state.messages.append(
            tool_result_message(
                state,
                execution,
                tool_call.id,
                source=source,
            )
        )

    save_state(state)


# --------------------------------------------------
# Resume pending approval
# --------------------------------------------------


def handle_pending_approval(state: AgentState) -> None:

    pending = state.pending_tool_call

    if pending is None:
        raise RuntimeError("Agent is waiting for approval but no pending tool call exists.")

    print("\nAgent is waiting for human approval.")

    print(f"Tool: {pending.tool_name}")

    print(f"Arguments: {pending.arguments}")

    approval = input("Approve this tool? [y/N]: ").strip().lower()

    tool_definition = tool_registry[pending.tool_name]

    if approval == "y":
        execution = execute_tool(pending.tool_name, pending.arguments, approved=True)

        process_tool_result(state, tool_definition, pending.arguments, execution)

    else:
        execution = ToolExecutionResult(
            status="denied",
            error=(f"Human rejected execution of '{pending.tool_name}'."),
        )

    print_tool_result(execution)

    source = None

    if execution.status == "success" and tool_definition.evidence is not None:
        source = resolve_evidence_source(
            tool_definition.evidence,
            pending.arguments,
        )

    state.messages.append(
        tool_result_message(
            state,
            execution,
            pending.tool_call_id,
            source=source,
        )
    )

    # Pending request is resolved

    state.pending_tool_call = None

    # Continue workflow

    state.status = "running"

    save_state(state)


# --------------------------------------------------
# Agent state machine
# --------------------------------------------------


def run_agent(state: AgentState) -> None:

    while state.step < state.max_steps:
        match state.status:
            case "running":
                run_agent_step(state)

            case "waiting_for_approval":
                print("\nAgent is paused waiting for approval.")

                save_state(state)

                break

            case "completed":
                print("\nAgent is already completed.")

                break

            case "failed":
                print("\nAgent has failed.")

                break

    else:
        state.status = "failed"

        save_state(state)

        print("\nAgent stopped: maximum number of steps reached.")
