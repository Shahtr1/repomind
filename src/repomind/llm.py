import json

import requests

from .config import MODEL, NUM_PREDICT, OLLAMA_TIMEOUT_SECONDS, OLLAMA_URL, TEMPERATURE
from .models import LLMResponse, LLMToolCall


def chat(
    messages: list[dict],
    tools: list[dict],
) -> LLMResponse:

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

    message = result["message"]

    tool_calls = [
        LLMToolCall(
            id=tool_call["id"],
            name=tool_call["function"]["name"],
            arguments=tool_call["function"]["arguments"],
        )
        for tool_call in message.get("tool_calls", [])
    ]
    done_reason = result.get("done_reason")

    if done_reason not in {"stop", "length"}:
        done_reason = "unknown"

    return LLMResponse(
        content=message.get("content", ""),
        tool_calls=tool_calls,
        finish_reason=done_reason,
    )
