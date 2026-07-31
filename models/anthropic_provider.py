import json
import logging
import uuid
from anthropic import AsyncAnthropic
from models.base import BaseProvider, ModelResponse, ToolCall
from agent.config import get_settings

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self):
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL

    def _convert_messages(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        system = None
        converted = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            elif msg["role"] == "tool":
                converted.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.get("tool_call_id", ""),
                            "content": msg["content"],
                        }
                    ],
                })
            elif msg["role"] == "assistant" and "tool_calls" in msg:
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"] if isinstance(tc, dict) else tc.name,
                        "input": tc["arguments"] if isinstance(tc, dict) else tc.arguments,
                    })
                converted.append({"role": "assistant", "content": content})
            else:
                converted.append({"role": msg["role"], "content": msg["content"]})
        return system, converted

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        converted = []
        for tool in tools:
            converted.append({
                "name": tool["function"]["name"],
                "description": tool["function"].get("description", ""),
                "input_schema": tool["function"].get("parameters", {"type": "object", "properties": {}}),
            })
        return converted

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> ModelResponse:
        system, converted_messages = self._convert_messages(messages)

        kwargs: dict = {
            "model": model or self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        response = await self.client.messages.create(**kwargs)

        content = None
        tool_calls = None
        for block in response.content:
            if block.type == "text":
                content = (content or "") + block.text
            elif block.type == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else {},
                ))

        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            },
        )

    async def is_available(self) -> bool:
        return bool(get_settings().ANTHROPIC_API_KEY)
