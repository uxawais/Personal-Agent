import logging

from openai import AsyncOpenAI

from agent.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI | None:
    global _client
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return None
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def embed_text(text: str) -> list[float]:
    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY not set; cannot generate embeddings")
    response = await client.embeddings.create(
        model=get_settings().EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
