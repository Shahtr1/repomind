import json

from .context.builder import (
    build_context,
    process_tool_result,
)
from .display import print_tool_result
from .evidence.store import resolve_evidence_source
from .executor import execute_tool
from .guardrails import check_completion
from .llm import chat
from .models import AgentState, PendingToolCall, ToolExecutionResult, AgentEvent
from .registry import tools, tool_registry
from .retrieval.parser import tool_result_message
from .state import save_state, next_sequence, create_message


# --------------------------------------------------
# One agent step
# --------------------------------------------------


def run_agent_step(state: AgentState) -> None:

    state.step += 1

    print(f"\n--- Agent step {state.step} ---")

    context = build_context(state)

    print("\nContext sent to LLM:")
    print(json.dumps(context, indent=2))

    assistant_message = chat(messages=context, tools=tools)

    print("\nAssistant message:")

    print(json.dumps(assistant_message, indent=2))

    # Persist assistant message in conversation

    state.messages.append(
        create_message(
            state,
            assistant_message,
        )
    )

    tool_calls = assistant_message.get("tool_calls", [])

    # --------------------------------------------------
    # Final answer
    # --------------------------------------------------

    if not tool_calls:

        guardrail = check_completion(
            state,
            assistant_message["content"],
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
        print(assistant_message["content"])

        state.status = "completed"

        save_state(state)

        return

    # --------------------------------------------------
    # Tool calls
    # --------------------------------------------------

    for tool_call in tool_calls:

        tool_name = tool_call["function"]["name"]

        tool_arguments = tool_call["function"]["arguments"]

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
                tool_call_id=tool_call["id"],
                tool_name=tool_name,
                arguments=tool_arguments,
            )

            state.status = "waiting_for_approval"

            save_state(state)

            print("\nAgent paused waiting " "for approval.")

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
                tool_call["id"],
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

        raise RuntimeError(
            "Agent is waiting for approval " "but no pending tool call exists."
        )

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
            error=(f"Human rejected execution " f"of '{pending.tool_name}'."),
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

                print("\nAgent is paused " "waiting for approval.")

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

        print("\nAgent stopped: " "maximum number of steps reached.")
