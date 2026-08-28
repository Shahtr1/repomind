from ..models import AgentEvent, AgentState, Evidence, Message
from .dependencies import is_incomplete_tool_call, resolve_tool_dependencies


def message_sources(
    messages: list[Message],
) -> set[str]:

    return {message.source for message in messages if message.source is not None}


def select_events(state: AgentState) -> list[AgentEvent]:
    selected = []

    # Keep the most recent event of each context-relevant type.
    latest_events: dict[str, AgentEvent] = {}

    for event in state.events:
        if event.type in {
            "guardrail_blocked",
            "generation_truncated",
        }:
            latest_events[event.type] = event

    selected.extend(latest_events.values())

    return sorted(
        selected,
        key=lambda event: event.sequence,
    )


def select_messages(
    state: AgentState,
    recent_limit: int = 10,
) -> list[Message]:

    # Messages explicitly marked as persistent must always remain
    # available to the model, regardless of the recent-message limit.
    persistent = [message for message in state.messages if message.persistent]

    # An assistant tool-call without all of its results represents
    # an incomplete interaction and must not be discarded.
    incomplete = [
        message
        for message in state.messages
        if is_incomplete_tool_call(
            message,
            state.messages,
        )
    ]

    # Use message IDs as the identity of a selected message.
    # This prevents the same message from being added more than once.
    selected_ids = {message.id for message in persistent + incomplete}

    # Everything not already required is eligible for the
    # recent-message window.
    candidates = [message for message in state.messages if message.id not in selected_ids]

    recent = candidates[-recent_limit:]

    selected_ids.update(message.id for message in recent)

    # Ensure assistant tool calls and their tool results
    # are always selected as one logical interaction.
    selected_ids = resolve_tool_dependencies(
        selected_ids,
        state.messages,
    )

    # Reconstruct the selected messages from the original state.
    selected = [message for message in state.messages if message.id in selected_ids]

    # Selection determines WHAT survives; sequence determines
    # WHERE it appears in the conversation.
    return sorted(
        selected,
        key=lambda message: message.sequence,
    )


def select_evidence(
    state: AgentState,
    selected_sources: set[str],
) -> list[Evidence]:

    # Evidence is only injected when its source is not already
    # represented by a selected conversation message.
    return [evidence for evidence in state.evidence if evidence.source not in selected_sources]
