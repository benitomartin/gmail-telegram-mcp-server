
import logging
import sys
from voice_agent.server.gmail_mcp_instance import gmail_mcp
from voice_agent.utils.logger_util import get_logger
from voice_agent.server.prompts.prompt_calls import *
from voice_agent.server.tools.get_emails import *
from voice_agent.server.tools.tts_reply import *

# Route logs to stderr; stdout reserved for JSON-RPC
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = get_logger(name="GmailServer")

for _name in [
    "mcp",
    "mcp.server",
    "mcp.server.lowlevel",
    "googleapiclient",
    "googleapiclient.discovery",
]:
    logging.getLogger(_name).setLevel(logging.ERROR)


def main() -> None:
    logger.info("Starting Gmail MCP server...")
    gmail_mcp.run()


if __name__ == "__main__":
    main()



# import logging
# from voice_agent.server.gmail_mcp_instance import gmail_mcp
# from voice_agent.utils.logger_util import get_logger
# from fastmcp import FastMCP


# # Route logs to stderr; stdout reserved for JSON-RPC
# logger = get_logger(name="GmailServer")

# class McpServersRegistry:
#     def __init__(self) -> None:
#         self.registry = FastMCP("tool_registry")
#         self._is_initialized = False

#     async def initialize(self) -> None:
#         if self._is_initialized:
#             return
        
#         logger.info("Initializing McpServersRegistry...")
#         await self.registry.import_server(server=gmail_mcp)
        
#         await self.registry.get_tools()
#         self._is_initialized = True
    
#     def get_registry(self) -> FastMCP:
#         if not self._is_initialized:
#             raise RuntimeError("McpServersRegistry is not initialized. Call 'initialize' first.")
#         return self.registry
        
        
# def main() -> None:
#     logger.info("Starting Gmail MCP Server...")
#     mcp_tool_manager = McpServersRegistry()
#     import asyncio
#     asyncio.run(mcp_tool_manager.initialize())
#     mcp_tool_manager.get_registry().run(
#         transport="stdio"
#     )
# if __name__ == "__main__":
#     main()
    