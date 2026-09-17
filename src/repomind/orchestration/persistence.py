from data.models import AgentState, LLMResponse

from ..state import create_message


def persist_assistant_response(
    state: AgentState,
    llm_response: LLMResponse,
) -> None:
    """
    Persist the assistant response in the agent timeline.

    The stored payload follows Ollama's message format so it can
    be sent back to Ollama during a later investigation step.
    """

    assistant_message: dict[str, object] = {
        "role": "assistant",
        "content": llm_response.content,
    }

    # Native tool calls must also be persisted because the next
    # Ollama request needs to know which tool the assistant requested.
    if llm_response.tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.name,
                    "arguments": tool_call.arguments,
                },
            }
            for tool_call in llm_response.tool_calls
        ]

        print(f"Tool calls: {len(llm_response.tool_calls)}")
    else:
        print(f"Content length: {len(llm_response.content)} characters")

    state.messages.append(
        create_message(
            state,
            assistant_message,
        )
    )
