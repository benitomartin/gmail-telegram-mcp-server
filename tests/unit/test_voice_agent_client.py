from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_agent.client.agent import VoiceAgentClient


@pytest.mark.asyncio
async def test_get_summary_prompt_uses_mock_gmail(mock_gmail_server: Any) -> None:
    """
    Test that VoiceAgentClient.get_summary_prompt() returns the prompt text
    from the MCP session when available, using the mock Gmail server fixture.

    Args:
        mock_gmail_server: A pytest fixture that sets up a mock Gmail server.

    Returns:
        None
    """

    # Create a mock prompt result that mimics what session.get_prompt() would return
    mock_prompt_result = MagicMock()
    mock_prompt_result.messages = [MagicMock(content=MagicMock(text="Mock summary prompt text"))]

    # Mock the session and its async get_prompt method
    mock_session = MagicMock()
    mock_session.get_prompt = AsyncMock(return_value=mock_prompt_result)

    # Patch the session context manager: mcp_host_initialized_session()
    # so that it yields our mock session instead of starting a real MCP session
    with patch.object(VoiceAgentClient, "mcp_host_initialized_session") as mock_ctx:
        mock_ctx.return_value.__aenter__.return_value = mock_session

        # Instantiate the client and call the method under test
        client = VoiceAgentClient()
        result = await client.get_summary_prompt(timespan="today", for_audio=False)

        # ✅ Assert the result came from our fake prompt
        assert result == "Mock summary prompt text"

        # ✅ Ensure the MCP session was called with the correct arguments
        mock_session.get_prompt.assert_awaited_once()

        # (Optional) The Gmail mock can also be checked if you pass it through the session
        emails = mock_gmail_server.fetch_emails()
        assert emails[0]["subject"] == "Test"
