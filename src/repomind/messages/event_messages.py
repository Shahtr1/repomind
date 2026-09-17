from ..data.constants import AgentEventType, LLMPhase
from ..data.models import AgentEvent


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

    if event.type == AgentEventType.GENERATION_TRUNCATED:
        if event.phase == LLMPhase.TOOL_USE:
            content = (
                "The previous tool-use generation reached the application's "
                "output limit before producing a complete response.\n\n"
                "Re-evaluate the investigation state. If repository inspection "
                "is still required, request the appropriate repository tool. "
                "Do not generate a final answer yet."
            )
        elif event.phase == LLMPhase.COMPLETION_DECISION:
            content = (
                "The previous completion-decision generation reached the "
                "application's output limit.\n\n"
                "Return a complete valid structured completion decision. "
                "Do not generate a final answer in this response."
            )
        elif event.phase == LLMPhase.FINAL_ANSWER:
            content = (
                "The previous final-answer generation reached the application's "
                "output limit.\n\n"
                "Continue the final answer from where it stopped. "
                "Do not restart or repeat the answer."
            )
        else:
            content = (
                "The previous model generation reached the application's "
                "output limit.\n\n"
                "Continue the investigation and follow the required response format."
            )

        return {
            "role": "user",
            "content": content,
        }

    return None
