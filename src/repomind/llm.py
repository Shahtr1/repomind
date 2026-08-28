import json

import requests

from .config import MODEL, NUM_PREDICT, OLLAMA_TIMEOUT_SECONDS, OLLAMA_URL, TEMPERATURE


def chat(
    messages: list[dict],
    tools: list[dict],
) -> dict:

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "temperature": TEMPERATURE,
            "num_predict": NUM_PREDICT,
            "think": False,
        },
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    result = response.json()

    print("\nFull Ollama response:")
    print(json.dumps(result, indent=2))

    return result
