import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from agent.config import get_settings
from agent.core import AgentCore
from models.router import ModelRouter
from memory.store import init_db
from channels.slack import SlackChannel
from channels.whatsapp import WhatsAppChannel
from channels.webchat import WebChatChannel
from api.webhooks import router as webhooks_router
from api.dashboard_api import router as dashboard_router
from api.websocket_api import router as websocket_router

import tools.web_search
import tools.url_reader
import tools.code_executor
import tools.creative_tools

logger = logging.getLogger(__name__)

_redis: Redis | None = None
_agent: AgentCore | None = None
_slack: SlackChannel | None = None
_whatsapp: WhatsAppChannel | None = None
_webchat: WebChatChannel | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis, _agent, _slack, _whatsapp, _webchat

    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))

    _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    await init_db()

    model_router = ModelRouter()
    _agent = AgentCore(_redis, model_router)

    _slack = SlackChannel()
    if await _slack.is_configured():
        _slack.set_agent(_agent)
        if _slack.socket_handler:
            await _slack.start_socket_mode()
            logger.info("Slack channel configured (Socket Mode)")
        else:
            logger.info("Slack channel configured (HTTP Mode)")
    else:
        logger.warning("Slack not configured (missing SLACK_BOT_TOKEN)")

    _whatsapp = WhatsAppChannel()
    if await _whatsapp.is_configured():
        _whatsapp.set_agent(_agent)
        logger.info("WhatsApp channel configured")
    else:
        logger.warning("WhatsApp not configured")

    _webchat = WebChatChannel()
    _webchat.set_agent(_agent)

    app.state.agent = _agent
    app.state.slack = _slack
    app.state.whatsapp = _whatsapp
    app.state.webchat = _webchat
    app.state.redis = _redis
    app.state.model_router = model_router

    available = await model_router.get_available_providers()
    logger.info(f"Available model providers: {available}")
    logger.info(f"Chorus Agent started on {settings.APP_HOST}:{settings.APP_PORT}")

    yield

    if _slack and _slack.socket_handler:
        await _slack.stop_socket_mode()
    await _redis.close()
    logger.info("Chorus Agent shut down")


app = FastAPI(title="Chorus Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(websocket_router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "chorus-agent"}
