import json

import requests

from .config import (
    MODEL,
    NUM_PREDICT,
    OLLAMA_TIMEOUT_SECONDS,
    OLLAMA_URL,
    TEMPERATURE,
)
from .models import LLMDecision, LLMResponse, LLMToolCall


def parse_llm_decision(content: str) -> LLMDecision | None:
    """
    Parse a structured completion decision from model-generated JSON.

    This function should only be called when the model was asked to
    return an LLMDecision.
    """

    if not content.strip():
        return None

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The model returned non-empty content, but it was not valid JSON for an LLMDecision."
        ) from exc

    return LLMDecision.model_validate(payload)


def chat(
    messages: list[dict],
    tools: list[dict],
    *,
    require_decision: bool = False,
) -> LLMResponse:
    """
    Send a request to Ollama and normalize its response.

    There are two modes.

    Tool mode:
        require_decision=False

        - Tools are available to the model.
        - No LLMDecision schema is forced.
        - The model can return native tool calls.

    Decision mode:
        require_decision=True

        - The LLMDecision JSON schema is sent to Ollama.
        - The model is expected to return a structured completion
          decision.
        - Tool calls should not be requested in this mode.
    """

    request_payload = {
        "model": MODEL,
        "messages": messages,
        "tools": tools,
        "stream": False,
        "temperature": TEMPERATURE,
        "num_predict": NUM_PREDICT,
        "think": False,
    }

    # Only enforce the decision schema when the application explicitly
    # asks for a completion decision.
    #
    # Do not enable this during ordinary tool investigation because
    # it can cause the model to describe a tool call as JSON instead
    # of producing a native tool_calls response.
    if require_decision:
        request_payload["format"] = LLMDecision.model_json_schema()

    response = requests.post(
        OLLAMA_URL,
        json=request_payload,
        timeout=OLLAMA_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    result = response.json()

    message = result["message"]

    print("\nNormalized Ollama message:")
    print(json.dumps(message, indent=2))

    tool_calls = [
        LLMToolCall(
            id=tool_call["id"],
            name=tool_call["function"]["name"],
            arguments=tool_call["function"]["arguments"],
        )
        for tool_call in message.get("tool_calls", [])
    ]

    content = message.get("content", "")

    decision = None

    # Only parse content as an LLMDecision when decision mode was
    # explicitly requested.
    #
    # In tool mode, content may be ordinary prose and should not be
    # incorrectly parsed as an LLMDecision.
    if require_decision and not tool_calls and content.strip():
        decision = parse_llm_decision(content)

    done_reason = result.get("done_reason")

    if done_reason not in {"stop", "length"}:
        done_reason = "unknown"

    return LLMResponse(
        content=content,
        tool_calls=tool_calls,
        finish_reason=done_reason,
        decision=decision,
    )
