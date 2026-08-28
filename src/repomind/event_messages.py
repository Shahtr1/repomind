from src.repomind.models import AgentEvent


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

    if event.type == "generation_truncated":
        return {
            "role": "user",
            "content": (
                "Your previous response was interrupted because "
                "generation reached the application's output limit.\n\n"
                "Continue the previous response from exactly where "
                "it stopped. Do not restart or repeat the answer."
            ),
        }

    return None
