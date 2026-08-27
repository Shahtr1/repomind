import os

from .agent import run_agent, handle_pending_approval
from .models import AgentState
from .state import STATE_FILE, load_state, save_state, create_message


def create_initial_state() -> AgentState:

    state = AgentState(messages=[])

    state.messages.append(
        create_message(
            state,
            {
                "role": "system",
                "content": """
                You are a repository investigation agent.

                When answering questions about the repository:

                1. Search for relevant information.
                2. Inspect the actual source corresponding to the retrieved information.
                3. Do not treat search results alone as sufficient evidence.
                4. Verify important claims against source material.
                5. Base the answer only on verified information.
                6. If the available evidence is insufficient, continue investigating.
                7. Never invent fields, behavior, or implementation details.
                """,
            },
            persistent=True,
        )
    )

    state.messages.append(
        create_message(
            state,
            {
                "role": "user",
                "content": """
                Explain how a tool call flows from the LLM to tool execution in this repository, including how approval-required tools are handled.

                Trace the implementation across the relevant source files. Do not answer until you have inspected the actual source code needed to explain the complete flow.
                """,
            },
            persistent=True,
        )
    )

    return state


def main() -> None:

    # --------------------------------------------------
    # Load existing workflow or create new one
    # --------------------------------------------------

    if os.path.exists(STATE_FILE):

        state = load_state()

        print(f"Loaded existing state: " f"{state.status}")

    else:

        state = create_initial_state()

        save_state(state)

        print("Created new agent state.")

    # --------------------------------------------------
    # Resume pending approval
    # --------------------------------------------------

    if state.status == "waiting_for_approval":

        handle_pending_approval(state)

    # --------------------------------------------------
    # Run workflow
    # --------------------------------------------------

    run_agent(state)


if __name__ == "__main__":
    main()
