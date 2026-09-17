from repomind.data.constants import LLMDecisionType, LLMFinishReason, LLMPhase
from repomind.data.models import AgentState

from ..context.builder import build_context
from ..llm import chat
from ..registry import tools
from .decisions import request_completion_decision, request_final_answer
from .persistence import persist_assistant_response
from .responses import (
    handle_cannot_complete,
    handle_final_answer,
    handle_generation_truncated,
    handle_missing_decision,
)
from .tool_calls import handle_tool_calls


def run_agent_step(state: AgentState) -> None:
    """Execute one agent iteration.

    The iteration has two possible LLM calls:
    1. Tool-use call: The model may request native repository tools.
    2. Completion-decision call: If no tools were requested, ask the model
       separately for a structured completion decision.
    """
    state.step += 1
    print(f"\n--- Agent step {state.step} ---")

    context = build_context(state)
    print(f"\nContext prepared: {len(context)} prompts")

    # ------------------------------------------------------------------
    # Phase 1: Tool-use call
    # ------------------------------------------------------------------
    llm_response = chat(
        messages=context,
        tools=tools,
        phase=LLMPhase.TOOL_USE,
    )

    print("\nAssistant tool-use response received:")
    print(f"Done reason: {llm_response.finish_reason}")

    if llm_response.finish_reason == LLMFinishReason.LENGTH:
        handle_generation_truncated(state, llm_response)
        return

    if llm_response.tool_calls:
        persist_assistant_response(state, llm_response)
        handle_tool_calls(
            state,
            llm_response.tool_calls,
        )
        return

    # We only persist native tool-call responses.
    #
    # The first no-tool response is not persisted because it may contain
    # ordinary intermediate prose.
    #
    # The completion decision is an internal control result, not a
    # conversation message, so it is kept in local Python variables.

    # ------------------------------------------------------------------
    # Phase 2: Completion-decision call
    # ------------------------------------------------------------------
    decision_response = request_completion_decision(state)
    print("\nAssistant completion-decision response received:")
    print(f"Done reason: {decision_response.finish_reason}")

    if decision_response.finish_reason == LLMFinishReason.LENGTH:
        handle_generation_truncated(state, decision_response)
        return

    decision = decision_response.decision

    if decision is None:
        handle_missing_decision(state)
        return

    if decision.decision == LLMDecisionType.CANNOT_COMPLETE:
        handle_cannot_complete(state, decision)
        return

    if decision.decision == LLMDecisionType.PROPOSE_FINAL_ANSWER:
        # ------------------------------------------------------------------
        # Phase 3: Final-answer generation
        # ------------------------------------------------------------------
        answer_response = request_final_answer(state)
        print("\nAssistant final-answer response received:")
        print(f"Done reason: {answer_response.finish_reason}")

        if answer_response.finish_reason == LLMFinishReason.LENGTH:
            handle_generation_truncated(state, answer_response)
            return

        handle_final_answer(state, answer_response.content)
