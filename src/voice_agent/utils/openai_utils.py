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

    Args:
            openai_client: The OpenAI client instance.
            model: The model name to use.
            messages: The list of messages for the chat completion.
            tools: Optional list of tools for tool-using models.
            tool_choice: Tool choice strategy, default is "auto".
            temperature: Sampling temperature, default is 0.2.

    Returns:
            The OpenAI API response as a dictionary.
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
