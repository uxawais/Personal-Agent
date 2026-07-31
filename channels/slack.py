import logging
import asyncio
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.adapter.starlette.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient
from channels.base import BaseChannel, IncomingMessage, OutgoingMessage
from agent.config import get_settings

logger = logging.getLogger(__name__)


class SlackChannel(BaseChannel):
    name = "slack"

    def __init__(self):
        settings = get_settings()
        self.app = AsyncApp(
            token=settings.SLACK_BOT_TOKEN,
            signing_secret=settings.SLACK_SIGNING_SECRET or "placeholder",
        )
        self.handler = AsyncSlackRequestHandler(self.app)
        self.socket_handler = None
        self._socket_task = None
        if settings.SLACK_APP_TOKEN:
            self.socket_handler = AsyncSocketModeHandler(self.app, settings.SLACK_APP_TOKEN)
        self._agent_core = None

    def set_agent(self, agent_core):
        self._agent_core = agent_core
        self._register_handlers()

    def _register_handlers(self):
        @self.app.event("app_mention")
        async def handle_mention(event, say):
            user_id = event["user"]
            text = event["text"]
            channel = event["channel"]
            thread_ts = event.get("thread_ts", event["ts"])

            if not await self._is_allowed(user_id):
                await say(text="Sorry, I'm not authorized to respond to you.", thread_ts=thread_ts)
                return

            response = await self._agent_core.process_message(
                user_message=text,
                conversation_id=f"slack:{channel}:{thread_ts}",
                channel="slack",
                user_id=user_id,
            )
            await say(text=response, thread_ts=thread_ts)

        @self.app.event("message")
        async def handle_dm(event, say):
            if event.get("channel_type") != "im":
                return
            if event.get("subtype"):
                return

            user_id = event["user"]
            text = event["text"]
            channel = event["channel"]

            if not await self._is_allowed(user_id):
                return

            response = await self._agent_core.process_message(
                user_message=text,
                conversation_id=f"slack:dm:{user_id}",
                channel="slack",
                user_id=user_id,
            )
            await say(text=response)

    async def _is_allowed(self, user_id: str) -> bool:
        settings = get_settings()
        allowed = settings.slack_allowed_user_ids_list
        if not allowed:
            return True
        return user_id in allowed

    async def send(self, message: OutgoingMessage) -> bool:
        try:
            await self.app.client.chat_postMessage(
                channel=message.user_id,
                text=message.content,
            )
            return True
        except Exception as e:
            logger.error(f"Slack send failed: {e}")
            return False

    async def start_socket_mode(self):
        if self.socket_handler:
            self._socket_task = asyncio.create_task(self.socket_handler.start_async())
            logger.info("Slack Socket Mode connected")

    async def stop_socket_mode(self):
        if self.socket_handler and self._socket_task:
            self._socket_task.cancel()
            logger.info("Slack Socket Mode disconnected")

    async def is_configured(self) -> bool:
        settings = get_settings()
        return bool(settings.SLACK_BOT_TOKEN and (settings.SLACK_SIGNING_SECRET or settings.SLACK_APP_TOKEN))

    def get_handler(self):
        return self.handler
