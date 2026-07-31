from abc import ABC, abstractmethod
from pydantic import BaseModel


class IncomingMessage(BaseModel):
    channel: str
    user_id: str
    conversation_id: str
    content: str
    metadata: dict = {}


class OutgoingMessage(BaseModel):
    channel: str
    user_id: str
    conversation_id: str
    content: str


class BaseChannel(ABC):
    name: str = "base"

    @abstractmethod
    async def send(self, message: OutgoingMessage) -> bool:
        ...

    @abstractmethod
    async def is_configured(self) -> bool:
        ...
