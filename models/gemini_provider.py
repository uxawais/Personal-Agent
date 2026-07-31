import json
import logging
import google.generativeai as genai
from models.base import BaseProvider, ModelResponse, ToolCall
from agent.config import get_settings

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    name = "gemini"

    def __init__(self):
        settings = get_settings()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def _convert_messages(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        system = None
        history = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            elif msg["role"] == "assistant":
                history.append({"role": "model", "parts": [msg["content"]]})
            elif msg["role"] == "tool":
                history.append({
                    "role": "user",
                    "parts": [{"function_response": {"name": msg.get("tool_call_id", ""), "response": {"result": msg["content"]}}}],
                })
            else:
                history.append({"role": "user", "parts": [msg["content"]]})
        return system, history

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> ModelResponse:
        system, history = self._convert_messages(messages)

        model_name = model or self.model_name
        genai_model = genai.GenerativeModel(
            model_name,
            system_instruction=system,
        )

        response = genai_model.generate_content(
            history,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

        content = response.text if response.text else None

        return ModelResponse(
            content=content,
            tool_calls=None,
            model=model_name,
            usage={
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if response.usage_metadata else 0,
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if response.usage_metadata else 0,
            },
        )

    async def is_available(self) -> bool:
        return bool(get_settings().GEMINI_API_KEY)
