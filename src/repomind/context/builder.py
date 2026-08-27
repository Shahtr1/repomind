from ..evidence.store import (
    add_tool_evidence,
    evidence_message,
    select_evidence,
)
from ..models import (
    AgentEvent,
    AgentState,
    ToolExecutionResult,
)
from .selection import message_sources, select_events, select_messages


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
