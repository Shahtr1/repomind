# Keep assistant tool calls and their tool results together.
from ..models import Message


def tool_call_ids(message: Message) -> set[str]:

    return {tool_call["id"] for tool_call in message.payload.get("tool_calls", [])}


def tool_result_id(message: Message) -> str | None:

    if message.payload.get("role") != "tool":
        return None

    return message.payload.get("tool_call_id")


def has_all_tool_results(
    assistant_message: Message,
    messages: list[Message],
) -> bool:

    required_ids = tool_call_ids(assistant_message)

    if not required_ids:
        return True

    # Tool results from other assistant messages may also exist
    # in state.messages, so we only check whether this message's
    # required tool-call IDs are all present.
    result_ids = {tool_result_id(message) for message in messages}

    return required_ids.issubset(result_ids)


def is_incomplete_tool_call(
    message: Message,
    messages: list[Message],
) -> bool:

    if not tool_call_ids(message):
        return False

    return not has_all_tool_results(
        message,
        messages,
    )


def related_tool_results(
    assistant_message: Message,
    messages: list[Message],
) -> list[Message]:

    call_ids = tool_call_ids(assistant_message)

    return [message for message in messages if tool_result_id(message) in call_ids]


def related_assistant_message(
    tool_result: Message,
    messages: list[Message],
) -> Message | None:

    tool_call_id = tool_result_id(tool_result)

    if tool_call_id is None:
        return None

    for message in messages:
        if tool_call_id in tool_call_ids(message):
            return message

    return None


def resolve_tool_dependencies(
    selected_ids: set[str],
    messages: list[Message],
) -> set[str]:

    resolved_ids = set(selected_ids)

    changed = True

    while changed:
        changed = False

        for message in messages:
            # If an assistant tool-call is selected, include
            # every corresponding tool result.
            if message.id in resolved_ids:
                call_ids = tool_call_ids(message)

                if call_ids:
                    for result in related_tool_results(
                        message,
                        messages,
                    ):
                        if result.id not in resolved_ids:
                            resolved_ids.add(result.id)
                            changed = True

            # If a tool result is selected, include the
            # assistant message that requested it.
            if message.id in resolved_ids:
                parent = related_assistant_message(
                    message,
                    messages,
                )

                if parent is not None and parent.id not in resolved_ids:
                    resolved_ids.add(parent.id)
                    changed = True

    return resolved_ids
