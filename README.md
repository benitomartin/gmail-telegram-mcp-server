To get GOOGLE_APPLICATION_CREDENTIALS

gcloud auth application-default login

# import logging

# import sys

# from voice_agent.server.gmail_mcp_instance import gmail_mcp

# from voice_agent.utils.logger_util import get_logger

# from voice_agent.server.prompts.prompt_calls import \*

# from voice_agent.server.tools.get_emails import \*

# from voice_agent.server.tools.tts_reply import \*

# # Route logs to stderr; stdout reserved for JSON-RPC

# logging.basicConfig(stream=sys.stderr, level=logging.INFO)

# logger = get_logger(name="GmailServer")

# for \_name in \[

# "mcp",

# "mcp.server",

# "mcp.server.lowlevel",

# "googleapiclient",

# "googleapiclient.discovery",

# \]:

# logging.getLogger(\_name).setLevel(logging.ERROR)

# def main() -> None:

# logger.info("Starting Gmail MCP server...")

# gmail_mcp.run()

# if __name__ == "__main__":

# main()
