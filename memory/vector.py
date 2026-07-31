import logging
import numpy as np
from memory.store import get_session, VectorMemory
from sqlalchemy import select, text

logger = logging.getLogger(__name__)


async def store_vector_memory(content: str, metadata: dict | None = None):
    import json
    async with await get_session() as session:
        entry = VectorMemory(
            content=content,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        session.add(entry)
        await session.commit()


async def search_vector_memory(query: str, limit: int = 5) -> list[dict]:
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
