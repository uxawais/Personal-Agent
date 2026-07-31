import json
import logging

from sqlalchemy import select

from memory.embeddings import embed_text
from memory.store import VectorMemory, get_session

logger = logging.getLogger(__name__)


async def store_vector_memory(content: str, metadata: dict[str, object] | None = None) -> None:
    embedding_json = None
    try:
        embedding = await embed_text(content)
        embedding_json = json.dumps(embedding)
    except Exception as e:
        logger.warning(f"Failed to embed content (storing without embedding): {e}")

    async with await get_session() as session:
        entry = VectorMemory(
            content=content,
            embedding=embedding_json,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        session.add(entry)
        await session.commit()


async def search_vector_memory(query: str, limit: int = 5) -> list[dict[str, object]]:
    embedding = None
    try:
        embedding = await embed_text(query)
    except Exception as e:
        logger.warning(f"Failed to embed query (falling back to chronological): {e}")

    if embedding is not None:
        try:
            return await _semantic_search(embedding, limit)
        except Exception as e:
            logger.warning(f"Vector search failed (falling back to chronological): {e}")

    return await _chronological_search(limit)


async def _semantic_search(embedding: list[float], limit: int) -> list[dict[str, object]]:
    distance = VectorMemory.embedding.cosine_distance(embedding)
    stmt = (
        select(VectorMemory, distance.label("distance"))
        .where(VectorMemory.embedding.isnot(None))
        .order_by(distance)
        .limit(limit)
    )
    async with await get_session() as session:
        result = await session.execute(stmt)
        rows = result.all()
        return [
            {
                "id": entry.id,
                "content": entry.content,
                "metadata": entry.metadata_json,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "score": float(dist) if dist is not None else None,
            }
            for entry, dist in rows
        ]


async def _chronological_search(limit: int) -> list[dict[str, object]]:
    async with await get_session() as session:
        stmt = select(VectorMemory).order_by(VectorMemory.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        entries = result.scalars().all()
        return [
            {
                "id": e.id,
                "content": e.content,
                "metadata": e.metadata_json,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ]
