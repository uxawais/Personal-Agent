import uuid
from datetime import datetime
from pydantic import BaseModel
from redis.asyncio import Redis


class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = None
    metadata: dict = {}

    def model_post_init(self, __context):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class Conversation:
    def __init__(self, redis: Redis, conversation_id: str | None = None, max_history: int = 50):
        self.redis = redis
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.max_history = max_history
        self._key = f"conv:{self.conversation_id}"

    async def add_message(self, role: str, content: str, metadata: dict | None = None) -> Message:
        msg = Message(role=role, content=content, metadata=metadata or {})
        await self.redis.rpush(self._key, msg.model_dump_json())
        await self.redis.ltrim(self._key, -self.max_history, -1)
        await self.redis.expire(self._key, 86400 * 7)
        return msg

    async def get_history(self, limit: int | None = None) -> list[Message]:
        n = limit or self.max_history
        raw = await self.redis.lrange(self._key, -n, -1)
        return [Message.model_validate_json(r) for r in raw]

    async def get_messages_for_model(self, limit: int = 20) -> list[dict]:
        history = await self.get_history(limit)
        return [{"role": m.role, "content": m.content} for m in history]

    async def clear(self):
        await self.redis.delete(self._key)

    async def message_count(self) -> int:
        return await self.redis.llen(self._key)
