from ..data.models import (
    AgentState,
    Evidence,
)
from ..messages.event_messages import event_message
from .selection import message_sources, select_events, select_evidence, select_messages


def build_context(state: AgentState) -> list[dict]:
    selected_messages = select_messages(state)

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


def evidence_message(evidence: Evidence) -> dict:

    return {
        "role": "system",
        "content": (
            f"Verified repository evidence\n\nSource: {evidence.source}\n\n{evidence.content}"
        ),
    }
