import pytest

from voice_agent.client.agent import VoiceAgentClient


@pytest.mark.asyncio
async def test_mcp_tools_and_prompts_count() -> None:
    """
    Test MCP client lists 3 prompts and 2 tools.

    Args:
        None
    Returns:
        None
    """
    async with VoiceAgentClient.mcp_host_initialized_session() as session:
        tools = await session.list_tools()
        prompts = await session.list_prompts()
        assert len(tools.tools) == 2, (
            f"Expected 2 tools, found {len(tools.tools)}: {[t.name for t in tools.tools]}"
        )
        assert len(prompts.prompts) == 3, (
            f"Expected 3 prompts, found {len(prompts.prompts)}: {[p.name for p in prompts.prompts]}"
        )
