from fastapi import APIRouter, Request
from pydantic import BaseModel

from agent.personality import PersonalityConfig, get_personality, set_personality
from memory.store import get_conversation_logs, get_memories
from memory.store import list_sessions as list_sessions_db
from tools.registry import get_registered_tools

router = APIRouter()


@router.get("/status")
async def get_status(request: Request):
    model_router = request.app.state.model_router
    providers = await model_router.get_available_providers()
    slack = request.app.state.slack
    whatsapp = request.app.state.whatsapp
    return {
        "status": "running",
        "model_providers": providers,
        "channels": {
            "slack": await slack.is_configured() if slack else False,
            "whatsapp": await whatsapp.is_configured() if whatsapp else False,
            "web": True,
        },
        "tools": get_registered_tools(),
    }


@router.get("/personality")
async def get_personality_config():
    return get_personality().model_dump()


@router.put("/personality")
async def update_personality(config: PersonalityConfig):
    set_personality(config)
    return {"status": "updated", "personality": config.model_dump()}


@router.get("/memories")
async def list_memories(category: str | None = None, limit: int = 20):
    return await get_memories(category, limit)


@router.get("/conversations")
async def list_conversations(conversation_id: str | None = None, limit: int = 50):
    return await get_conversation_logs(conversation_id, limit)


@router.get("/sessions")
async def list_sessions(limit: int = 50):
    return await list_sessions_db(limit=limit)


@router.get("/tools")
async def list_tools():
    return {"tools": get_registered_tools()}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user_id: str = "dashboard"


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    agent = request.app.state.agent
    response = await agent.process_message(
        user_message=body.message,
        conversation_id=body.conversation_id,
        channel="dashboard",
        user_id=body.user_id,
    )
    return {"response": response}
