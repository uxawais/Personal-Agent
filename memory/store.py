import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, func, Integer
from datetime import datetime
from agent.config import get_settings

logger = logging.getLogger(__name__)


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
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


_engine = None
_session_factory = None


async def init_db():
    global _engine, _session_factory
    settings = get_settings()
    _engine = create_async_engine(settings.DATABASE_URL, echo=False)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


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
