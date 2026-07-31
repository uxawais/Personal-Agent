import logging
from models.base import BaseProvider, ModelResponse
from models.openai_provider import OpenAIProvider
from models.anthropic_provider import AnthropicProvider
from models.bedrock_provider import BedrockProvider
from models.gemini_provider import GeminiProvider
from models.openrouter_provider import OpenRouterProvider
from agent.config import get_settings

logger = logging.getLogger(__name__)

COMPLEX_KEYWORDS = ["analyze", "build", "create", "design", "write", "plan", "architect", "debug", "refactor"]


class ModelRouter:
    def __init__(self):
        self.providers: dict[str, BaseProvider] = {}
        self._init_providers()

    def _init_providers(self):
        provider_classes = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "bedrock": BedrockProvider,
            "gemini": GeminiProvider,
            "openrouter": OpenRouterProvider,
        }
        for name, cls in provider_classes.items():
            try:
                provider = cls()
                self.providers[name] = provider
            except Exception as e:
                logger.warning(f"Failed to init {name} provider: {e}")

    def _select_provider(self, messages: list[dict], force_provider: str | None = None) -> tuple[str, BaseProvider, str | None]:
        model = None
        if force_provider and force_provider in self.providers:
            return force_provider, self.providers[force_provider], model

        settings = get_settings()
        strategy = settings.ROUTING_STRATEGY

        if strategy == "smart":
            last_msg = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_msg = msg["content"].lower()
                    break

            is_complex = any(kw in last_msg for kw in COMPLEX_KEYWORDS) or len(last_msg) > 500

            if is_complex:
                for name in ["anthropic", "openai", "openrouter", "bedrock"]:
                    if name in self.providers:
                        return name, self.providers[name], model
            else:
                for name in ["openrouter", "openai", "gemini", "bedrock"]:
                    if name in self.providers:
                        provider = self.providers[name]
                        if hasattr(provider, "cheap_model") and provider.cheap_model:
                            model = provider.cheap_model
                        return name, provider, model

        default = settings.DEFAULT_PROVIDER
        if default in self.providers:
            return default, self.providers[default], model

        for name, provider in self.providers.items():
            return name, provider, model

        raise RuntimeError("No model providers available. Check your API keys.")

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        force_provider: str | None = None,
    ) -> ModelResponse:
        provider_name, provider, model = self._select_provider(messages, force_provider)
        logger.info(f"Routing to {provider_name}" + (f" model={model}" if model else ""))

        try:
            return await provider.complete(messages, tools, max_tokens, temperature, model=model)
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")
            for fallback_name, fallback_provider in self.providers.items():
                if fallback_name == provider_name:
                    continue
                try:
                    logger.info(f"Falling back to {fallback_name}")
                    return await fallback_provider.complete(messages, tools, max_tokens, temperature)
                except Exception as fallback_error:
                    logger.error(f"Fallback {fallback_name} also failed: {fallback_error}")
                    continue
            raise RuntimeError("All model providers failed")

    async def get_available_providers(self) -> list[str]:
        available = []
        for name, provider in self.providers.items():
            if await provider.is_available():
                available.append(name)
        return available
