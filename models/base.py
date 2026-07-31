from abc import ABC, abstractmethod
from pydantic import BaseModel


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict


class ModelResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    model: str = ""
    usage: dict = {}


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> ModelResponse:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...
