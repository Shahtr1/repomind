from ..models import AgentState
from ..state import save_state
from .runner import run_agent_step


def run_agent(state: AgentState) -> None:
    """
    Run the agent state machine until it completes, fails,
    waits for approval, or reaches the maximum step count.
    """

    while state.step < state.max_steps:
        match state.status:
            case "running":
                run_agent_step(state)

            case "waiting_for_approval":
                print("\nAgent is paused waiting for approval.")

                save_state(state)

                break

            case "completed":
                print("\nAgent is already completed.")

                break

            case "failed":
                print("\nAgent has failed.")

                break

    else:
        state.status = "failed"

        save_state(state)

        print("\nAgent stopped: maximum number of steps reached.")
