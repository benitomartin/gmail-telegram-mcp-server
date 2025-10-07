# from voice_agent.server.gmail_mcp_instance import gmail_mcp
from voice_agent.server.prompts.email_prompts import (
    EMAIL_ASSISTANT_SYSTEM_PROMPT,
    EMAIL_SUMMARY_AUDIO_PROMPT,
    EMAIL_SUMMARY_PROMPT,
)


# @gmail_mcp.prompt(
#     name="email_assistant_system_prompt",
#     description="System prompt for the email assistant agent with automatic tool selection.",
# )
def email_assistant_system_prompt() -> str:
    """
    System prompt for the email assistant agent with automatic tool selection.

    Args:
            None

    Returns:
            The system prompt string.
    """
    return EMAIL_ASSISTANT_SYSTEM_PROMPT


# @gmail_mcp.prompt(
#     name="email_summary_format_prompt",
#     description="Prompt for formatting email summaries with a specific timespan.",
# )
def email_summary_format_prompt(timespan: str = "today") -> str:
    """
    Prompt for formatting email summaries with a specific timespan.

    Args:
            timespan: The timespan for the email summary (e.g., "today", "yesterday").

    Returns:
            The formatted email summary prompt string.
    """
    return EMAIL_SUMMARY_PROMPT.format(timespan=timespan)


# @gmail_mcp.prompt(
#     name="email_summary_audio_format_prompt",
#     description="Prompt for formatting email summaries specifically for audio/speech output.",
# )
def email_summary_audio_format_prompt(timespan: str = "today") -> str:
    """
    Prompt for formatting email summaries specifically for audio/speech output.

    Args:
            timespan: The timespan for the email summary (e.g., "today", "yesterday").

    Returns:
            The formatted email summary audio prompt string.
    """
    return EMAIL_SUMMARY_AUDIO_PROMPT.format(timespan=timespan)
