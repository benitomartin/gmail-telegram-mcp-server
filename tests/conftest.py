from typing import Any

import pytest

from voice_agent.server.gmail_server import GmailMcpServer


@pytest.fixture
def mock_gmail_server() -> Any:
    """
    Mock Gmail MCP server for testing.

    Args:
        None

    Returns:
        An instance of a mock GmailMcpServer.
    """

    class MockGmailMcpServer(GmailMcpServer):
        def fetch_emails(self) -> list[dict[str, str]]:
            return [{"subject": "Test", "body": "Email"}]

    return MockGmailMcpServer()
