from typing import Literal

from fastmcp import FastMCP
from fastmcp.prompts import Prompt
from fastmcp.tools import Tool

from voice_agent.config import settings
from voice_agent.server.prompts.prompt_calls import (
    email_assistant_system_prompt,
    email_summary_audio_format_prompt,
    email_summary_format_prompt,
)
from voice_agent.server.tools.get_emails import get_emails
from voice_agent.server.tools.tts_reply import tts_instagram_audio
from voice_agent.utils.logger_util import get_logger

logger = get_logger(name="GmailServer")


class GmailMcpServer:
    def __init__(self, name: str = "Gmail MCP Server"):
        self.logger = logger
        self.mcp = FastMCP(name=name)
        self._register_tools()
        self._register_prompts()

    def _register_tools(self) -> None:
        self.mcp.add_tool(
            Tool.from_function(
                name=settings.tools.get_emails_tool,
                description=(
                    "Fetch emails from Gmail for a specified number of days. "
                    "Returns JSON array of emails with id, from, subject, date, and body fields."
                ),
                fn=get_emails,
            )
        )
        self.mcp.add_tool(
            Tool.from_function(
                name=settings.tools.tts_instagram_audio_tool,
                description="Convert text to speech for Instagram audio messages.",
                fn=tts_instagram_audio,
            )
        )

    def _register_prompts(self) -> None:
        self.mcp.add_prompt(
            Prompt.from_function(
                name=settings.prompts.assistant_prompt,
                description=(
                    "System prompt for the email assistant agent with automatic tool selection."
                ),
                fn=email_assistant_system_prompt,
            )
        )
        self.mcp.add_prompt(
            Prompt.from_function(
                name=settings.prompts.summary_prompt,
                description="Prompt for formatting email summaries with a specific timespan.",
                fn=email_summary_format_prompt,
            )
        )
        self.mcp.add_prompt(
            Prompt.from_function(
                name=settings.prompts.summary_audio_prompt,
                description=(
                    "Prompt for formatting email summaries specifically for audio/speech output."
                ),
                fn=email_summary_audio_format_prompt,
            )
        )

    def run(
        self,
        transport: Literal["stdio", "http", "streamable-http"] | None = "stdio",
    ) -> None:
        """
        Run the MCP server with the specified transport.

        Args:
            transport: The transport method to use ("stdio", "http", or "streamable-http").

        Returns:
            None
        """
        self.logger.info(f"Starting {self.mcp.name}...")
        # Log tools and prompts before starting the server
        try:
            # Use synchronous access if available, otherwise fallback to async
            tools = self.mcp.get_tools_sync() if hasattr(self.mcp, "get_tools_sync") else None
            prompts = self.mcp.get_prompts_sync() if hasattr(self.mcp, "get_prompts_sync") else None
            if tools is not None and prompts is not None:
                self.logger.info(f"Tool registered sync: {tools.keys()}")
                self.logger.info(f"Prompt registered sync: {prompts.keys()}")
            else:
                import asyncio

                async def log_tools_and_prompts() -> None:
                    tools = await self.mcp.get_tools()
                    prompts = await self.mcp.get_prompts()
                    self.logger.info(f"Tool registered async: {tools.keys()}")
                    self.logger.info(f"Prompt registered async: {prompts.keys()}")

                asyncio.run(log_tools_and_prompts())
        except Exception as e:
            self.logger.error(f"Error logging tools/prompts: {e}")
        self.mcp.run(
            transport=transport,
        )


def main() -> None:
    """
    Main entry point to run the Gmail MCP server.

    Args:
        None

    Return:
        None
    """
    server = GmailMcpServer()
    server.run(
        transport="stdio",
    )


if __name__ == "__main__":
    main()
