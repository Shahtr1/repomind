from ..context.builder import build_context
from ..llm import chat
from ..models import AgentState, LLMResponse


def request_completion_decision(
    state: AgentState,
) -> LLMResponse:
    """
    Ask the model whether the investigation can be completed.

    This is a separate LLM call from the tool-use call.

    No tools are supplied here because the model must evaluate the
    evidence already collected rather than request another tool.

    The LLMDecision JSON schema is enforced by require_decision=True.
    """

    context = build_context(state)

    print("\nRequesting structured completion decision...")

    return chat(
        messages=context,
        tools=[],
        require_decision=True,
    )
