import logging
import httpx
from channels.base import BaseChannel, IncomingMessage, OutgoingMessage
from agent.config import get_settings

logger = logging.getLogger(__name__)


class WhatsAppChannel(BaseChannel):
    name = "whatsapp"

    def __init__(self):
        self._agent_core = None
        self._base_url = "https://graph.facebook.com/v19.0"

    def set_agent(self, agent_core):
        self._agent_core = agent_core

    async def _is_allowed(self, phone_number: str) -> bool:
        settings = get_settings()
        allowed = settings.whatsapp_allowed_numbers_list
        if not allowed:
            return True
        return phone_number in allowed

    async def handle_webhook(self, payload: dict) -> str | None:
        settings = get_settings()
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            messages = value.get("messages", [])
            if not messages:
                return None

            for msg in messages:
                from_number = msg.get("from", "")
                if not await self._is_allowed(from_number):
                    logger.warning(f"Unauthorized WhatsApp message from {from_number}")
                    continue

                msg_type = msg.get("type", "")
                content = ""
                if msg_type == "text":
                    content = msg.get("text", {}).get("body", "")
                elif msg_type == "image":
                    content = f"[Image received: {msg.get('image', {}).get('caption', 'no caption')}]"
                elif msg_type == "audio":
                    content = "[Audio message received]"
                else:
                    content = f"[Unsupported message type: {msg_type}]"

                if content and self._agent_core:
                    response = await self._agent_core.process_message(
                        user_message=content,
                        conversation_id=f"whatsapp:{from_number}",
                        channel="whatsapp",
                        user_id=from_number,
                    )
                    await self._send_text(from_number, response)

        except Exception as e:
            logger.error(f"WhatsApp webhook error: {e}")
        return None

    async def _send_text(self, to: str, text: str):
        settings = get_settings()
        url = f"{self._base_url}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text[:4096]},
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                logger.error(f"WhatsApp send failed: {response.status_code} {response.text}")

    async def send(self, message: OutgoingMessage) -> bool:
        try:
            await self._send_text(message.user_id, message.content)
            return True
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return False

    async def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)
