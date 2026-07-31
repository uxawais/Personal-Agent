import pytest
from tools.registry import register_tool, get_tool_schemas, execute_tool, get_registered_tools


def test_register_tool():
    @register_tool(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {"x": {"type": "string"}}},
    )
    async def test_tool(x: str) -> str:
        return f"result: {x}"

    assert "test_tool" in get_registered_tools()

    schemas = get_tool_schemas()
    test_schema = next((s for s in schemas if s["function"]["name"] == "test_tool"), None)
    assert test_schema is not None
    assert test_schema["function"]["description"] == "A test tool"


@pytest.mark.asyncio
async def test_execute_tool():
    @register_tool(name="add_numbers", description="Add two numbers")
    async def add_numbers(a: int, b: int) -> int:
        return a + b

    result = await execute_tool("add_numbers", {"a": 3, "b": 4})
    assert result == 7


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    with pytest.raises(ValueError, match="Unknown tool"):
        await execute_tool("nonexistent_tool_xyz", {})
