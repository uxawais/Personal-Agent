import json
import logging
import boto3
from models.base import BaseProvider, ModelResponse, ToolCall
from agent.config import get_settings

logger = logging.getLogger(__name__)


class BedrockProvider(BaseProvider):
    name = "bedrock"

    def __init__(self):
        settings = get_settings()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        self.model = settings.BEDROCK_MODEL

    def _build_request(self, messages, tools, max_tokens, temperature, model):
        system = None
        conv_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                conv_messages.append(msg)

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": conv_messages,
        }
        if system:
            body["system"] = system
        if tools:
            body["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {"type": "object", "properties": {}}),
                }
                for t in tools
            ]
        return body, model or self.model

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> ModelResponse:
        body, model_id = self._build_request(messages, tools, max_tokens, temperature, model)

        response = self.client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
        )

        result = json.loads(response["body"].read())

        content = None
        tool_calls = None
        for block in result.get("content", []):
            if block["type"] == "text":
                content = (content or "") + block["text"]
            elif block["type"] == "tool_use":
                if tool_calls is None:
                    tool_calls = []
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    arguments=block.get("input", {}),
                ))

        usage = result.get("usage", {})
        return ModelResponse(
            content=content,
            tool_calls=tool_calls,
            model=self.model,
            usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
            },
        )

    async def is_available(self) -> bool:
        settings = get_settings()
        return bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
