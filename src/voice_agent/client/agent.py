import json as _json
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

from voice_agent.config import settings
from voice_agent.server.prompts.email_prompts import (
    EMAIL_ASSISTANT_SYSTEM_PROMPT,
    EMAIL_SUMMARY_AUDIO_PROMPT,
    EMAIL_SUMMARY_PROMPT,
)
from voice_agent.utils.logger_util import get_logger
from voice_agent.utils.openai_utils import get_openai_completion


class VoiceAgentClient:
    def __init__(self, openai_client: OpenAI | None = None, model: str | None = None):
        self.logger = get_logger("VoiceAgentClient")

        self.openai_client = openai_client
        self.model = model

    @staticmethod
    def _server_params() -> StdioServerParameters:
        return StdioServerParameters(
            command="python", args=["-m", "voice_agent.server.gmail_server"]
        )

    @staticmethod
    @asynccontextmanager
    async def mcp_host_initialized_session() -> Any:
        """
        Context manager that yields an MCP ClientSession connected to a voice agent server.
        The server is started as a subprocess using stdio communication.

        Args:
                None

        Yields:
                An initialized ClientSession connected to the MCP server.
        """
        server_params = VoiceAgentClient._server_params()
        async with (
            stdio_client(server_params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            yield session

    async def get_summary_prompt(
        self, timespan: str = "today", for_audio: bool = False, session: Any = None
    ) -> str:
        """
        Get the email summary prompt from the MCP server, or use a fallback if not available.

        Args:
                timespan: The timespan to include in the summary (default: "today").
                for_audio: Whether to get the audio format prompt (default: False).

        Returns:
                The email summary prompt string.
        """
        if session is None:
            async with self.mcp_host_initialized_session() as session:
                try:
                    prompt_name = (
                        settings.prompts.summary_audio_prompt
                        if for_audio
                        else settings.prompts.summary_prompt
                    )
                    prompt_result = await session.get_prompt(
                        prompt_name, arguments={"timespan": timespan}
                    )
                    if prompt_result.messages:
                        return prompt_result.messages[0].content.text
                except Exception as e:
                    self.logger.error(f"Error getting summary prompt: {e}")
                # Fallback prompt
                fallback = EMAIL_SUMMARY_AUDIO_PROMPT if for_audio else EMAIL_SUMMARY_PROMPT
                return fallback.format(timespan=timespan)
        else:
            try:
                prompt_name = (
                    settings.prompts.summary_audio_prompt
                    if for_audio
                    else settings.prompts.summary_prompt
                )
                prompt_result = await session.get_prompt(
                    prompt_name, arguments={"timespan": timespan}
                )
                if prompt_result.messages:
                    return prompt_result.messages[0].content.text
            except Exception as e:
                self.logger.error(f"Error getting summary prompt: {e}")
            # Fallback prompt
            fallback = EMAIL_SUMMARY_AUDIO_PROMPT if for_audio else EMAIL_SUMMARY_PROMPT
            return fallback.format(timespan=timespan)

    async def run_agentic_query(self, user_query: str) -> tuple[str, str | None]:
        """
        Run an agentic query against the MCP server.

        Args:
                user_query: The user's query string.

        Returns:
                A tuple containing the final response string and optional base64-encoded audio.
        """
        if not self.openai_client or not self.model:
            raise ValueError("OpenAI client and model must be set for agentic queries.")
        async with self.mcp_host_initialized_session() as session:
            mcp_tools = await session.list_tools()
            oa_tools = []
            for tool in mcp_tools.tools:
                oa_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or f"Execute {tool.name}",
                            "parameters": tool.inputSchema
                            if tool.inputSchema
                            else {
                                "type": "object",
                                "properties": {},
                                "additionalProperties": False,
                            },
                        },
                    }
                )

            try:
                mcp_prompts = await session.list_prompts()
                system_prompt_obj = None
                for prompt in mcp_prompts.prompts:
                    if prompt.name == settings.prompts.assistant_prompt:
                        prompt_result = await session.get_prompt(prompt.name)
                        if prompt_result.messages:
                            system_prompt_obj = prompt_result.messages[0].content.text
                        break
                system_msg = (
                    system_prompt_obj if system_prompt_obj else EMAIL_ASSISTANT_SYSTEM_PROMPT
                )
            except Exception:
                system_msg = EMAIL_ASSISTANT_SYSTEM_PROMPT

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_query},
            ]

            audio_b64 = None
            for _ in range(4):
                completion = get_openai_completion(
                    openai_client=self.openai_client,
                    model=self.model,
                    messages=messages,
                    tools=oa_tools,
                    tool_choice="auto",
                    temperature=0.2,
                )
                choice = completion.choices[0].message  # type: ignore
                if hasattr(choice, "tool_calls") and choice.tool_calls:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": getattr(choice, "content", "") or "",
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments,
                                    },
                                }
                                for tc in choice.tool_calls
                            ],
                        }
                    )
                    for tc in choice.tool_calls:
                        tool_name = tc.function.name
                        try:
                            args = _json.loads(tc.function.arguments or "{}")
                        except Exception:
                            args = {}
                        try:
                            tool_result = await session.call_tool(tool_name, arguments=args)
                            result_text = (
                                tool_result.content[0].text
                                if getattr(tool_result, "content", None)
                                else str(tool_result)
                            )
                            if tool_name == "tts_instagram_audio":
                                audio_b64 = result_text
                                result_text = "[Audio generated successfully]"
                        except Exception as e:
                            result_text = f"ERROR: {str(e)}"
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tool_name,
                                "content": result_text,
                            }
                        )
                    continue
                return (getattr(choice, "content", "") or "", audio_b64)
            return ("Sorry, I couldn't complete the request.", None)
