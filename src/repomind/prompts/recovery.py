from ..data.constants import LLMPhase


def generation_recovery_instruction(
    phase: LLMPhase | None,
) -> str:
    if phase == LLMPhase.TOOL_USE:
        return (
            "The previous tool-use generation was truncated. "
            "Re-evaluate the current investigation state. "
            "If repository inspection is still required, issue the appropriate "
            "tool call directly. Do not generate a final answer yet."
        )

    if phase == LLMPhase.COMPLETION_DECISION:
        return (
            "The previous completion-decision generation was truncated. "
            "Return one complete valid completion decision. "
            "Do not generate a final answer in this response."
        )

    if phase == LLMPhase.FINAL_ANSWER:
        return (
            "The previous final-answer generation was truncated. "
            "Continue the answer from where it stopped without restarting."
        )

    return (
        "The previous model generation was truncated. "
        "Continue according to the current execution phase."
    )
