from data.constants import LLMPhase
from data.models import AgentState, LLMResponse

from ..context.builder import build_context
from ..llm import chat


def request_completion_decision(
    state: AgentState,
) -> LLMResponse:
    """
    Ask the model whether the investigation can be completed.

    This call returns a small structured LLMDecision.
    """

    context = build_context(state)

    print("\nRequesting structured completion decision...")

    return chat(
        messages=context,
        tools=[],
        require_decision=True,
        phase=LLMPhase.COMPLETION_DECISION,
    )


def request_final_answer(
    state: AgentState,
) -> LLMResponse:
    """
    Ask the model to generate the final answer as ordinary text.

    No JSON decision schema is used here.
    """

    context = build_context(state)

    final_answer_instruction = {
        "role": "system",
        "content": (
            "Generate the final answer to the user's original question. "
            "Use the verified repository evidence available in the context. "
            "Do not request tools. "
            "Do not describe the investigation process unless it is relevant "
            "to the answer. "
            "Return only the final answer in ordinary text."
        ),
    }

    final_answer_context = [
        final_answer_instruction,
        *context,
    ]

    print("\nRequesting final answer...")

    return chat(
        messages=final_answer_context,
        tools=[],
        require_decision=False,
        phase=LLMPhase.FINAL_ANSWER,
    )
