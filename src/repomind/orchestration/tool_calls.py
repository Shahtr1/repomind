from repomind.data.constants import AgentStatus, ToolExecutionStatus
from repomind.data.models import AgentState, PendingToolCall

from ..executor import execute_tool
from ..registry import tool_registry
from ..state import save_state
from ..tool_results import process_tool_result
from .execution_results import record_execution_result


def handle_tool_calls(
    state: AgentState,
    tool_calls,
) -> None:
    """
    Execute the tool calls returned by the model.

    Approval handling remains inside this function because approval
    changes the agent state and may pause the current execution.
    """

    for tool_call in tool_calls:
        tool_name = tool_call.name
        tool_arguments = tool_call.arguments

        print(f"\nTool requested: {tool_name}")
        print("Arguments:", tool_arguments)

        execution = execute_tool(
            tool_name,
            tool_arguments,
        )

        tool_definition = tool_registry[tool_name]

        process_tool_result(
            state,
            tool_definition,
            tool_arguments,
            execution,
        )

        if execution.status == ToolExecutionStatus.APPROVAL_REQUIRED:
            state.pending_tool_call = PendingToolCall(
                tool_call_id=tool_call.id,
                tool_name=tool_name,
                arguments=tool_arguments,
            )

            state.status = AgentStatus.WAITING_FOR_APPROVAL

            save_state(state)

            print("\nAgent paused waiting for approval.")

            return

        record_execution_result(
            state,
            tool_definition,
            tool_arguments,
            execution,
            tool_call.id,
        )

    save_state(state)
