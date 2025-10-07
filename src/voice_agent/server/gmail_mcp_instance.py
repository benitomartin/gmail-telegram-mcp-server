from fastmcp import FastMCP
from voice_agent.utils.logger_util import get_logger

logger = get_logger(name="GmailServer")

gmail_mcp = FastMCP(
    name="Gmail MCP Server",
)
