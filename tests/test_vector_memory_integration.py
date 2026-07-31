import os

import pytest
from sqlalchemy import delete

from agent.config import get_settings
from memory import store
from memory import vector as vector_module

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set "
    "(e.g. postgresql+asyncpg://chorus:chorus@localhost:5432/chorus)",
)


@pytest.mark.asyncio
async def test_semantic_ranking() -> None:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not set; cannot generate embeddings")
    settings.DATABASE_URL = os.environ["TEST_DATABASE_URL"]

    store._engine = None
    store._session_factory = None
    try:
        await store.init_db()  # type: ignore[no-untyped-call]
    except Exception as e:
        pytest.skip(f"Postgres not reachable: {e}")

    async with await store.get_session() as session:
        await session.execute(delete(store.VectorMemory))
        await session.commit()

    await vector_module.store_vector_memory(
        "Client in Lahore wants a chatbot for their restaurant menu"
    )
    await vector_module.store_vector_memory("The weather today is sunny with a chance of rain")

    results = await vector_module.search_vector_memory("chatbot for a restaurant", limit=5)
    assert len(results) >= 2, "expected both entries to be stored and searchable"
    assert (
        "restaurant" in str(results[0]["content"])
    ), "semantically relevant entry should rank first"
