from ..display import print_tool_result
from ..evidence.store import resolve_evidence_source
from ..models import AgentState, ToolDefinition, ToolExecutionResult
from ..tool_messages import tool_result_message


def record_execution_result(
    state: AgentState,
    tool_definition: ToolDefinition,
    tool_arguments: dict,
    execution: ToolExecutionResult,
    tool_call_id: str,
) -> None:
    """
    Record a completed tool execution in the agent conversation.

    This function does not execute tools or manage approval state.
    """

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
            tool_call_id,
            source=source,
        )
    )
