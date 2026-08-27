# config.py
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5:9b"

MAX_SEARCH_RESULTS = 50

IGNORED_DIRECTORIES = {".git", ".venv", "node_modules", "__pycache__"}

IGNORED_FILES = {"agent_state.json", "agent_note.txt"}

# converts the relative path into an absolute path.
REPOSITORY_ROOT = Path(".").resolve()

TEMPERATURE = 0

MAX_STEPS = 8
