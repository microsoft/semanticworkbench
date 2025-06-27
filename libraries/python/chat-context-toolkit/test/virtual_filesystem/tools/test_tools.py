import pytest
from chat_context_toolkit.virtual_filesystem.tools import ToolCollection
from openai.types.chat import ChatCompletionMessageToolCallParam, ChatCompletionToolParam


async def test_execute_nonexistent_tool_raises_error():
    """Test that executing a non-existent tool raises ValueError."""
    tools = ToolCollection([])

    tool_call = ChatCompletionMessageToolCallParam(
        id="test", function={"name": "nonexistent_tool", "arguments": "{}"}, type="function"
    )

    # Non-existent tool should raise ValueError
    with pytest.raises(ValueError, match="Tool not found"):
        await tools.execute_tool(tool_call)


async def test_execute_tool_delegates_to_tool():
    class Tool1:
        @property
        def tool_param(self) -> ChatCompletionToolParam:
            return {"type": "function", "function": {"name": "tool1", "description": "Tool 1"}}

        async def execute(self, args: dict) -> str:
            return "tool1 executed"

    class Tool2:
        @property
        def tool_param(self) -> ChatCompletionToolParam:
            return {"type": "function", "function": {"name": "tool2", "description": "Tool 2"}}

        async def execute(self, args: dict) -> str:
            return "tool2 executed"

    tools = ToolCollection([Tool1(), Tool2()])

    # Both tools should be available
    assert len(tools) == 2
    assert tools.has_tool("tool1")
    assert tools.has_tool("tool2")

    # Both tools should be executable
    result1 = await tools.execute_tool(
        ChatCompletionMessageToolCallParam(id="test1", function={"name": "tool1", "arguments": "{}"}, type="function")
    )
    assert result1 == "tool1 executed"

    result2 = await tools.execute_tool(
        ChatCompletionMessageToolCallParam(id="test2", function={"name": "tool2", "arguments": "{}"}, type="function")
    )
    assert result2 == "tool2 executed"
