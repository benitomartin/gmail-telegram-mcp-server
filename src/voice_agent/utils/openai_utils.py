"""
Utility for OpenAI chat completions requests.
"""

from typing import Any


def get_openai_completion(
    openai_client: Any,
    model: str,
    messages: list[dict],
    tools: list | None = None,
    tool_choice: str = "auto",
    temperature: float = 0.2,
) -> dict:
    """
    Wrapper for OpenAI chat.completions.create.
    Returns the completion object.
    """
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools is not None:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
    return openai_client.chat.completions.create(**kwargs)
