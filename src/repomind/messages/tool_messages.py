import json

from data.models import AgentState, Message, ToolExecutionResult

from src.repomind.state import create_message

# Makes the execution outcome visible to the LLM


def tool_result_message(
    state: AgentState,
    execution: ToolExecutionResult,
    tool_call_id: str,
    source: str | None = None,
) -> Message:

    return create_message(
        state,
        {
            "role": "tool",
            "content": json.dumps(execution.model_dump()),
            "tool_call_id": tool_call_id,
        },
        source=source,
    )
