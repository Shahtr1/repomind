from ..context.builder import build_context
from ..llm import chat
from ..models import AgentState
from ..registry import tools
from .decisions import request_completion_decision
from .persistence import persist_assistant_response
from .responses import (
    handle_generation_truncated,
    handle_llm_response,
)


def run_agent_step(state: AgentState) -> None:
    """
    Execute one agent iteration.

    The iteration has two possible LLM calls:

    1. Tool-use call:
       The model may request native repository tools.

    2. Completion-decision call:
       If no tools were requested, ask the model separately for a
       structured completion decision.
    """

    state.step += 1

    print(f"\n--- Agent step {state.step} ---")

    context = build_context(state)

    print(f"\nContext prepared: {len(context)} messages")

    # --------------------------------------------------
    # Phase 1: Tool-use call
    # --------------------------------------------------

    llm_response = chat(
        messages=context,
        tools=tools,
    )

    print("\nAssistant tool-use response received:")
    print(f"Done reason: {llm_response.finish_reason}")

    # A truncated generation is incomplete.
    # Record the truncation event, but do not persist the
    # incomplete assistant response as normal conversation context.
    if llm_response.finish_reason == "length":
        handle_generation_truncated(
            state,
            llm_response,
        )

        return

    # If the model requested tools, persist and execute that response.
    if llm_response.tool_calls:
        persist_assistant_response(
            state,
            llm_response,
        )

        handle_llm_response(
            state,
            llm_response,
        )

        return

    # We do not persist the first no-tool response because it may contain
    # ordinary prose such as: "I need to inspect the repository further."
    # That response is not a valid investigation event or final answer,
    # and persisting it would pollute the next context.
    # We only persist native tool-call responses and structured
    # completion-decision responses.

    # --------------------------------------------------
    # Phase 2: Completion-decision call
    # --------------------------------------------------

    # Do not treat ordinary content from the tool-use call as a final
    # answer. Ask for a separate structured decision instead.
    decision_response = request_completion_decision(
        state,
    )

    print("\nAssistant completion-decision response received:")
    print(f"Done reason: {decision_response.finish_reason}")

    # A truncated completion decision is incomplete.
    # Record the truncation event, but do not persist the
    # incomplete structured response as normal conversation context.
    if decision_response.finish_reason == "length":
        handle_generation_truncated(
            state,
            decision_response,
        )

        return

    # Persist only a complete structured completion decision.
    persist_assistant_response(
        state,
        decision_response,
    )

    handle_llm_response(
        state,
        decision_response,
    )
