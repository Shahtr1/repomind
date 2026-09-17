import json

from .context.builder import evidence_message
from .context.dependencies import (
    is_incomplete_tool_call,
    resolve_tool_dependencies,
)
from .context.selection import select_evidence
from .data.constants import AgentEventType, ToolExecutionStatus
from .data.models import (
    AgentEvent,
    AgentState,
    Message,
    SearchMatch,
    SearchResult,
    ToolDefinition,
    ToolExecutionResult,
)
from .evidence.store import add_tool_evidence
from .state import create_message


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


def event_message(event: AgentEvent) -> dict | None:

    if event.type == AgentEventType.GUARDRAIL_BLOCKED:
        return {
            "role": "user",
            "content": (
                "Your attempted answer was blocked by "
                "an application guardrail.\n\n"
                f"Reason: {event.reason}\n"
                f"Required action: {event.required_action}\n\n"
                "Continue investigating using the available "
                "repository tools. Do not provide a final "
                "answer until the requirement is satisfied."
            ),
        }

    return None


def select_events(state: AgentState) -> list[AgentEvent]:

    return sorted(
        state.events,
        key=lambda event: event.sequence,
    )


def parse_search_results(query: str, result: str) -> SearchResult:

    matches = []

    for line in result.splitlines():
        try:
            location, content = line.split(": ", maxsplit=1)

            path, line_number = location.rsplit(":", maxsplit=1)

            matches.append(SearchMatch(path=path, line_number=int(line_number), content=content))

        except ValueError:
            continue

    return SearchResult(query=query, matches=matches)


def add_search_result(state: AgentState, query: str, result: str) -> None:

    search_result = parse_search_results(query, result)

    state.retrieval_results.append(search_result)


def process_tool_result(
    state: AgentState,
    tool_definition: ToolDefinition,
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


def message_sources(
    messages: list[Message],
) -> set[str]:

    return {message.source for message in messages if message.source is not None}


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


def build_context(state: AgentState) -> list[dict]:

    selected_messages = select_messages(
        state,
    )

    print("\nSelected messages:")

    for message in selected_messages:
        print(
            f"sequence={message.sequence} "
            f"role={message.payload.get('role')} "
            f"source={message.source} "
            f"persistent={message.persistent}"
        )

    selected_sources = message_sources(selected_messages)

    selected_evidence = select_evidence(
        state,
        selected_sources,
    )

    context_items = []

    for message in selected_messages:
        context_items.append((message.sequence, message.payload))

    for event in select_events(state):
        payload = event_message(event)

        if payload is not None:
            context_items.append((event.sequence, payload))

    context_items.sort(key=lambda item: item[0])

    context = [payload for _, payload in context_items]

    for evidence in selected_evidence:
        context.append(evidence_message(evidence))

    return context
