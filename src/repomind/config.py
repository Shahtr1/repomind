from pathlib import Path

# --------------------------------------------------
# Ollama / LLM
# --------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL = "qwen3.5:9b"

TEMPERATURE = 0

NUM_PREDICT = 1000

OLLAMA_TIMEOUT_SECONDS = 120


# --------------------------------------------------
# Repository
# --------------------------------------------------

# Converts the relative project path into an absolute path.
REPOSITORY_ROOT = Path(".").resolve()

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
}

IGNORED_FILES = {
    "agent_state.json",
    "agent_note.txt",
}


# --------------------------------------------------
# Retrieval
# --------------------------------------------------

MAX_SEARCH_RESULTS = 50


# --------------------------------------------------
# Agent
# --------------------------------------------------

MAX_STEPS = 15
