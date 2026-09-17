from data.constants import AgentStatus
from data.models import AgentState

from ..state import save_state
from .runner import run_agent_step


def run_agent(state: AgentState) -> None:
    """
    Run the agent state machine until it completes, fails,
    waits for approval, or reaches the maximum step count.
    """

    while state.step < state.max_steps:
        match state.status:
            case AgentStatus.RUNNING:
                run_agent_step(state)

            case AgentStatus.WAITING_FOR_APPROVAL:
                print("\nAgent is paused waiting for approval.")

                save_state(state)

                break

            case AgentStatus.COMPLETED:
                print("\nAgent is already completed.")

                break

            case AgentStatus.FAILED:
                print("\nAgent has failed.")

                break

    else:
        state.status = AgentStatus.FAILED

        save_state(state)

        print("\nAgent stopped: maximum number of steps reached.")
