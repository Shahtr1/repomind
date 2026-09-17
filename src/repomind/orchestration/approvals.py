# --------------------------------------------------
# Resume pending approval
# --------------------------------------------------
from ..data.constants import AgentStatus, ToolExecutionStatus
from ..data.models import AgentState, ToolExecutionResult
from ..executor import execute_tool
from ..registry import tool_registry
from ..state import save_state
from ..tool_results import process_tool_result
from .execution_results import record_execution_result


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
            status=ToolExecutionStatus.DENIED,
            error=f"Human rejected execution of '{pending.tool_name}'.",
        )

    record_execution_result(
        state,
        tool_definition,
        pending.arguments,
        execution,
        pending.tool_call_id,
    )

    # Pending request is resolved

    state.pending_tool_call = None

    # Continue workflow

    state.status = AgentStatus.RUNNING

    save_state(state)
