import logging
from channels.base import BaseChannel, OutgoingMessage
from agent.config import get_settings

logger = logging.getLogger(__name__)


class WebChatChannel(BaseChannel):
    name = "web"

    def __init__(self):
        self._agent_core = None
        self._connections: dict[str, list] = {}

    def set_agent(self, agent_core):
        self._agent_core = agent_core

    def add_connection(self, user_id: str, websocket):
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def remove_connection(self, user_id: str, websocket):
        if user_id in self._connections:
            self._connections[user_id] = [ws for ws in self._connections[user_id] if ws != websocket]
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def handle_message(self, user_id: str, content: str) -> str:
        if not self._agent_core:
            return "Agent not initialized"

        response = await self._agent_core.process_message(
            user_message=content,
            conversation_id=f"web:{user_id}",
            channel="web",
            user_id=user_id,
        )

        for ws in self._connections.get(user_id, []):
            try:
                await ws.send_json({"type": "message", "content": response})
            except Exception as e:
                logger.error(f"WebSocket send failed: {e}")

        return response

    async def send(self, message: OutgoingMessage) -> bool:
        for ws in self._connections.get(message.user_id, []):
            try:
                await ws.send_json({"type": "message", "content": message.content})
                return True
            except Exception as e:
                logger.error(f"WebSocket send failed: {e}")
        return False

    async def is_configured(self) -> bool:
        return True
