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


def openrouter_slug_for(model: str) -> str | None:
    lowered = model.lower()
    if "/" in lowered or ":" in lowered:
        return None
    if lowered.startswith("gpt-"):
        return f"openai/{lowered}"
    if "claude" in lowered:
        return f"anthropic/{lowered}"
    if "gemini" in lowered:
        return f"google/{lowered}"
    if "deepseek" in lowered:
        return f"deepseek/{lowered}"
    return None


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

    def _provider_available(self, name: str) -> bool:
        if name not in self.providers:
            return False
        settings = get_settings()
        key_map = {
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
            "bedrock": settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY,
            "gemini": settings.GEMINI_API_KEY,
            "openrouter": settings.OPENROUTER_API_KEY,
        }
        return bool(key_map.get(name))

    def _select_provider(self, messages: list[dict], force_provider: str | None = None, force_model: str | None = None) -> tuple[str, BaseProvider, str | None]:
        model = None
        if force_model:
            provider_name = self._provider_for_model(force_model)
            resolved_model = force_model
            if provider_name == "openrouter":
                slug = openrouter_slug_for(force_model)
                if slug:
                    resolved_model = slug
            return provider_name, self.providers[provider_name], resolved_model
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
                    if self._provider_available(name):
                        return name, self.providers[name], model
            else:
                for name in ["openrouter", "openai", "gemini", "bedrock"]:
                    if self._provider_available(name):
                        provider = self.providers[name]
                        if hasattr(provider, "cheap_model") and provider.cheap_model:
                            model = provider.cheap_model
                        return name, provider, model

        default = settings.DEFAULT_PROVIDER
        if self._provider_available(default):
            return default, self.providers[default], model

        for name, provider in self.providers.items():
            if self._provider_available(name):
                return name, provider, model
        for name, provider in self.providers.items():
            return name, provider, model

        raise RuntimeError("No model providers available. Check your API keys.")

    def _provider_for_model(self, model: str) -> str:
        lowered = model.lower()

        if "openrouter" in lowered and self._provider_available("openrouter"):
            return "openrouter"

        if "claude" in lowered and self._provider_available("anthropic"):
            return "anthropic"
        if "bedrock" in lowered and self._provider_available("bedrock"):
            return "bedrock"
        if "gemini" in lowered and self._provider_available("gemini"):
            return "gemini"
        if lowered.startswith(("gpt-", "text-embedding-", "o1-", "o3-")) and self._provider_available("openai"):
            return "openai"

        if ("/" in lowered or ":" in lowered) and self._provider_available("openrouter"):
            return "openrouter"

        settings = get_settings()
        defaults = {
            "openrouter": settings.OPENROUTER_MODEL,
            "openai": settings.OPENAI_MODEL,
            "anthropic": settings.ANTHROPIC_MODEL,
            "gemini": settings.GEMINI_MODEL,
            "bedrock": settings.BEDROCK_MODEL,
        }
        for name, default in defaults.items():
            if model == default and self._provider_available(name):
                return name
        if self._provider_available("openrouter"):
            return "openrouter"
        for name in self.providers:
            if self._provider_available(name):
                return name
        for name in self.providers:
            return name
        raise RuntimeError("No model providers available for forced model")

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        force_provider: str | None = None,
        force_model: str | None = None,
    ) -> ModelResponse:
        provider_name, provider, model = self._select_provider(messages, force_provider, force_model)
        logger.info(f"Routing to {provider_name}" + (f" model={model}" if model else ""))

        try:
            return await provider.complete(messages, tools, max_tokens, temperature, model=model)
        except Exception as e:
            logger.error(f"Provider {provider_name} failed: {e}")
            if force_model:
                for fallback_name, fallback_provider in self.providers.items():
                    if fallback_name == provider_name or fallback_name != "openrouter":
                        continue
                    try:
                        logger.info(f"Retrying forced model via {fallback_name}")
                        return await fallback_provider.complete(
                            messages, tools, max_tokens, temperature, model=model or force_model
                        )
                    except Exception as fallback_error:
                        logger.error(f"Fallback {fallback_name} also failed: {fallback_error}")
                        continue
                raise RuntimeError(
                    f"Model '{force_model}' failed on all providers. "
                    f"Last error: {e}"
                )
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
