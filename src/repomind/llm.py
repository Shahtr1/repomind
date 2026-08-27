import requests

from .config import OLLAMA_URL, MODEL, TEMPERATURE


def chat(messages: list, tools: list) -> dict:

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "tools": tools,
            "stream": False,
            "temperature": TEMPERATURE
        }
    )

    response.raise_for_status()

    result = response.json()

    return result["message"]