import pytest

from voice_agent.client.agent import VoiceAgentClient


@pytest.mark.asyncio
async def test_voice_agent_end_to_end_mcp() -> None:
    """
    Integration test: ensure VoiceAgentClient can initialize an MCP session,
    list real tools and prompts, and fetch a real prompt text.

    Args:
        None

    Returns:
        None
    """

    # Initialize a real MCP session (not mocked)
    async with VoiceAgentClient.mcp_host_initialized_session() as session:
        # ✅ Step 1: List tools
        tools = await session.list_tools()
        assert len(tools.tools) > 0, "Expected at least one tool registered"
        tool_names = [t.name for t in tools.tools]
        assert "get_emails" in tool_names or any("email" in n for n in tool_names)

        # ✅ Step 2: List prompts
        prompts = await session.list_prompts()
        assert len(prompts.prompts) > 0, "Expected at least one prompt registered"
        prompt_names = [p.name for p in prompts.prompts]
        assert any("summary" in name for name in prompt_names)

        # ✅ Step 3: Call get_summary_prompt() through the real client
        client = VoiceAgentClient()
        prompt_text = await client.get_summary_prompt(timespan="today", for_audio=False)
        assert isinstance(prompt_text, str)
        assert "today" in prompt_text.lower() or len(prompt_text) > 0
