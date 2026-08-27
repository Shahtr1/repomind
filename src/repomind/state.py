import uuid

from .models import AgentState, Message

STATE_FILE = "agent_state.json"


def save_state(state: AgentState, path: str = STATE_FILE) -> None:

    with open(path, "w", encoding="utf-8") as file:
        file.write(state.model_dump_json(indent=2))


def load_state(path: str = STATE_FILE) -> AgentState:

    with open(path, encoding="utf-8") as file:
        return AgentState.model_validate_json(file.read())


def next_sequence(state: AgentState) -> int:

    state.sequence += 1

    return state.sequence


def create_message(
    state: AgentState,
    payload: dict,
    source: str | None = None,
    persistent: bool = False,
) -> Message:

    return Message(
        id=str(uuid.uuid4()),
        sequence=next_sequence(state),
        payload=payload,
        source=source,
        persistent=persistent,
    )
