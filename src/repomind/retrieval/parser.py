import json

from ..context.selection import (
    message_sources,
    select_events,
    select_messages,
)
from ..evidence.store import (
    add_tool_evidence,
    evidence_message,
    select_evidence,
)
from ..models import (
    AgentEvent,
    AgentState,
    Message,
    SearchMatch,
    SearchResult,
    ToolExecutionResult,
)
from ..state import create_message


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

    if event.type == "guardrail_blocked":
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
    tool_definition,
    tool_arguments: dict,
    execution: ToolExecutionResult,
) -> None:

    if execution.status != "success":
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


def build_context(state: AgentState) -> list[dict]:

    # Use a tiny window temporarily so we can force older tool results
    # out of the conversation and verify evidence fallback.
    selected_messages = select_messages(
        state,
        recent_limit=2,
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
