import os

from repomind.data.constants import AgentStatus
from repomind.data.models import AgentState

from .orchestration import run_agent
from .orchestration.approvals import handle_pending_approval
from .state import STATE_FILE, create_message, load_state, save_state


def create_initial_state() -> AgentState:
    state = AgentState(messages=[])

    state.messages.append(
        create_message(
            state,
            {
                "role": "system",
                "content": """
                You are a repository investigation agent.

                Your responsibility is to investigate repository questions using
                available repository tools and verified source evidence.

                Investigation rules:

                1. Search for relevant information before making implementation claims.
                2. Inspect the actual source corresponding to search results.
                3. Search results alone are not evidence.
                4. Verify important claims against source material.
                5. Do not invent fields, behavior, files, or implementation details.
                6. Continue investigating when the available evidence is insufficient.
                7. The application, not the model, controls execution and completion.
                8. Never assume that stopping generation means the investigation is complete.

                Tool usage rules:

                1. If repository information or another available capability is needed,
                   call the appropriate tool immediately.
                2. Select tools using their dynamically provided names, descriptions,
                   and argument schemas.
                3. Do not describe a tool call in response content.
                4. Do not write a function-like string such as "some_tool()" as a
                   substitute for a native tool call.
                5. Do not invent tool names or arguments.
                6. If no available tool can provide the required information,
                   explain the limitation.
                7. Only propose a final answer after the relevant information has
                   been inspected and verified.
                8. Do not return continue_investigation merely to describe a tool
                   that should be called.

                Response rules:

                - If repository information is needed, use a native tool call.
                - Do not return a structured decision merely to describe a future tool call.
                - Do not write a function-like string such as "some_tool()" as a
                  substitute for a native tool call.
                - When you have enough verified evidence to answer, return a structured
                  decision with decision = "propose_final_answer".
                - When the required information cannot be obtained, return a structured
                  decision with decision = "cannot_complete".
                - Do not return ordinary prose outside the structured response.
                - Do not claim that an answer is final unless the relevant source code
                  has been inspected and the answer is supported by evidence.

                Structured response shape for a decision:

                {
                  "decision": "propose_final_answer"
                                | "cannot_complete",
                  "reason": "string",
                }

                Field rules:
                
                - propose_final_answer:
                    reason must explain why the evidence is sufficient.
                
                - cannot_complete:
                    reason must explain the limitation.

                Important:

                The structured decision format is used only when the model is making
                a completion decision.
                
                When repository investigation is required, use a native tool call.
                Do not represent tool calls as ordinary response content.

                The application will validate tool names and arguments, enforce
                policy, execute tools, record evidence, and control agent state.
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
                Where is the agent completion decision implemented, and what prevents incomplete answers?
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

        print(f"Loaded existing state: {state.status}")

    else:
        state = create_initial_state()

        save_state(state)

        print("Created new agent state.")

    # --------------------------------------------------
    # Resume pending approval
    # --------------------------------------------------

    if state.status == AgentStatus.WAITING_FOR_APPROVAL:
        handle_pending_approval(state)

    # --------------------------------------------------
    # Run workflow
    # --------------------------------------------------

    run_agent(state)


if __name__ == "__main__":
    main()
