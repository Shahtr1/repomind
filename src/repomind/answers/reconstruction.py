from ..models import AgentState


def collect_answer_fragments(state: AgentState) -> str:
    """
    Reconstruct the current answer artifact from consecutive assistant
    generations connected by generation_truncated events.

    Timeline example:

        assistant fragment A
        generation_truncated
        assistant fragment B
        generation_truncated
        assistant fragment C

    becomes:

        fragment A + fragment B + fragment C
    """

    timeline = []

    for message in state.messages:
        timeline.append(
            (
                message.sequence,
                "message",
                message,
            )
        )

    for event in state.events:
        timeline.append(
            (
                event.sequence,
                "event",
                event,
            )
        )

    timeline.sort(key=lambda item: item[0])

    fragments = []

    # Start from the newest item and collect the final assistant fragment.
    index = len(timeline) - 1

    if index < 0:
        return ""

    sequence, item_type, item = timeline[index]

    if item_type != "message":
        return ""

    payload = item.payload

    if (
        payload.get("role") != "assistant"
        or payload.get("tool_calls")
        or not payload.get("content", "").strip()
    ):
        return ""

    fragments.append(payload["content"])

    index -= 1

    # Walk backwards through:
    #
    # generation_truncated
    # assistant fragment
    #
    # pairs.
    while index >= 1:
        _, event_type, event = timeline[index]

        if event_type != "event" or event.type != "generation_truncated":
            break

        _, previous_type, previous_item = timeline[index - 1]

        if previous_type != "message":
            break

        previous_payload = previous_item.payload

        if (
            previous_payload.get("role") != "assistant"
            or previous_payload.get("tool_calls")
            or not previous_payload.get("content", "").strip()
        ):
            break

        fragments.append(previous_payload["content"])

        index -= 2

    # We collected fragments backwards.
    fragments.reverse()

    return "".join(fragments)
