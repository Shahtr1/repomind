from ..data.constants import AgentEventType
from ..data.models import AgentEvent
from .recovery import generation_recovery_instruction


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
        return {
            "role": "user",
            "content": (
                "The previous model generation reached the application's "
                "output limit.\n\n"
                f"Required action: "
                f"{generation_recovery_instruction(event.phase)}"
            ),
        }

    return None
