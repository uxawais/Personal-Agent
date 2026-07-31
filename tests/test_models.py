import pytest
from models.base import ModelResponse, ToolCall


def test_model_response():
    resp = ModelResponse(
        content="Hello!",
        model="gpt-4o",
        usage={"prompt_tokens": 10, "completion_tokens": 5},
    )
    assert resp.content == "Hello!"
    assert resp.tool_calls is None


def test_model_response_with_tools():
    resp = ModelResponse(
        content=None,
        tool_calls=[
            ToolCall(id="call_1", name="web_search", arguments={"query": "test"}),
        ],
        model="gpt-4o",
    )
    assert resp.content is None
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "web_search"
    assert resp.tool_calls[0].arguments == {"query": "test"}
