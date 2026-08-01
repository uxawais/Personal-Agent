import logging
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text, func, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from agent.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 1536


class Base(DeclarativeBase):
    pass


class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    key: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="conversation")
    importance: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(255), index=True)
    channel: Mapped[str] = mapped_column(String(50))
    user_id: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VectorMemory(Base):
    __tablename__ = "vector_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=True
    )
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ConversationTitle(Base):
    __tablename__ = "conversation_titles"

    conversation_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


_engine = None
_session_factory = None


async def init_db():
    global _engine, _session_factory
    settings = get_settings()
    _engine = create_async_engine(settings.DATABASE_URL, echo=False)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _upgrade_schema()
    logger.info("Database initialized")


async def _upgrade_schema() -> None:
    if _engine is None:
        return
    try:
        async with _engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(
                text(
                    "ALTER TABLE vector_memory "
                    "ALTER COLUMN embedding TYPE vector(1536) "
                    "USING embedding::vector"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_vector_memory_hnsw "
                    "ON vector_memory USING hnsw (embedding vector_cosine_ops)"
                )
            )
    except Exception as e:
        logger.warning(f"Schema upgrade failed (continuing without it): {e}")


async def get_session() -> AsyncSession:
    if _session_factory is None:
        await init_db()
    return _session_factory()


async def save_memory(category: str, key: str, content: str, source: str = "conversation", importance: int = 5):
    async with await get_session() as session:
        entry = MemoryEntry(category=category, key=key, content=content, source=source, importance=importance)
        session.add(entry)
        await session.commit()


async def get_memories(category: str | None = None, limit: int = 20) -> list[dict]:
    async with await get_session() as session:
        from sqlalchemy import select
        stmt = select(MemoryEntry).order_by(MemoryEntry.importance.desc(), MemoryEntry.created_at.desc())
        if category:
            stmt = stmt.where(MemoryEntry.category == category)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        entries = result.scalars().all()
        return [{"id": e.id, "category": e.category, "key": e.key, "content": e.content, "importance": e.importance} for e in entries]


async def log_conversation(conversation_id: str, channel: str, user_id: str, role: str, content: str, model_used: str | None = None, tokens_used: int = 0):
    async with await get_session() as session:
        log = ConversationLog(
            conversation_id=conversation_id,
            channel=channel,
            user_id=user_id,
            role=role,
            content=content,
            model_used=model_used,
            tokens_used=tokens_used,
        )
        session.add(log)
        await session.commit()


async def get_conversation_logs(conversation_id: str | None = None, limit: int = 50) -> list[dict]:
    async with await get_session() as session:
        from sqlalchemy import select
        stmt = select(ConversationLog).order_by(ConversationLog.created_at.desc())
        if conversation_id:
            stmt = stmt.where(ConversationLog.conversation_id == conversation_id)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        logs = result.scalars().all()
        return [
            {
                "id": l.id,
                "conversation_id": l.conversation_id,
                "channel": l.channel,
                "user_id": l.user_id,
                "role": l.role,
                "content": l.content,
                "model_used": l.model_used,
                "tokens_used": l.tokens_used,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]


async def delete_session(conversation_id: str) -> None:
    async with await get_session() as session:
        from sqlalchemy import delete
        await session.execute(
            delete(ConversationLog).where(
                ConversationLog.conversation_id == conversation_id
            )
        )
        await session.commit()


async def get_conversation_title(conversation_id: str) -> str | None:
    async with await get_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(ConversationTitle.title).where(
                ConversationTitle.conversation_id == conversation_id
            )
        )
        return result.scalar()


async def set_conversation_title(conversation_id: str, title: str) -> None:
    async with await get_session() as session:
        from sqlalchemy import select
        entry = (
            await session.execute(
                select(ConversationTitle).where(
                    ConversationTitle.conversation_id == conversation_id
                )
            )
        ).scalar_one_or_none()
        if entry is None:
            session.add(
                ConversationTitle(conversation_id=conversation_id, title=title)
            )
        else:
            entry.title = title
        await session.commit()


async def list_sessions(channel: str = "dashboard", limit: int = 50) -> list[dict[str, object]]:
    async with await get_session() as session:
        stmt = text(
            """
            SELECT s.conversation_id, s.last_message, s.last_at, s.message_count, t.title
            FROM (
                SELECT conversation_id,
                       MAX(created_at) AS last_at,
                       COUNT(*) AS message_count,
                       (SELECT content FROM conversation_logs c2
                        WHERE c2.conversation_id = c1.conversation_id
                        ORDER BY c2.id DESC LIMIT 1) AS last_message
                FROM conversation_logs c1
                WHERE channel = :channel
                GROUP BY conversation_id
            ) s
            LEFT JOIN conversation_titles t ON t.conversation_id = s.conversation_id
            ORDER BY s.last_at DESC
            LIMIT :limit
            """
        ).bindparams(channel=channel, limit=limit)
        result = await session.execute(stmt)
        rows = result.mappings().all()
        return [
            {
                "conversation_id": row["conversation_id"],
                "last_message": row["last_message"],
                "last_at": row["last_at"].isoformat() if row["last_at"] else None,
                "message_count": row["message_count"],
                "title": row["title"],
            }
            for row in rows
        ]
