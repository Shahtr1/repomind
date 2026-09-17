from data.constants import ToolExecutionStatus
from data.models import AgentState, ToolExecutionResult

from .evidence.store import add_tool_evidence


def process_tool_result(
    state: AgentState,
    tool_definition,
    tool_arguments: dict,
    execution: ToolExecutionResult,
) -> None:
    if execution.status != ToolExecutionStatus.SUCCESS:
        return

    if execution.result is None:
        return

    if tool_definition.evidence is not None:
        add_tool_evidence(state, tool_definition.evidence, tool_arguments, execution.result)

    if tool_definition.search is not None:
        search_result = tool_definition.search.result_parser(
            tool_arguments["query"], execution.result
        )

        state.retrieval_results.append(search_result)
