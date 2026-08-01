from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent.config import get_settings
from agent.personality import PersonalityConfig, get_personality, set_personality
from memory.store import (
    delete_session,
    get_conversation_logs,
    get_conversation_title,
    get_memories,
    save_memory,
    set_conversation_title,
)
from memory.store import list_sessions as list_sessions_db
from tools.registry import get_registered_tools

import asyncio
import httpx

TITLE_FILLER_WORDS = {
    "please", "help", "me", "can", "you", "could", "would", "the", "a", "an",
    "i", "my", "for", "with", "and", "to", "of", "on", "in", "about", "is",
    "are", "do", "does", "what", "how", "need", "want", "like", "write",
}

_models_cache: dict = {"all": None, "at": None}


async def _fetch_openrouter_models() -> list[dict]:
    settings = get_settings()
    if not settings.OPENROUTER_API_KEY:
        return []
    now = asyncio.get_event_loop().time()
    if _models_cache["all"] is not None and _models_cache["at"] is not None:
        if now - _models_cache["at"] < 600:
            return _models_cache["all"]
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            )
            resp.raise_for_status()
            raw = resp.json().get("data", [])
        all_models = [
            {
                "id": m["id"],
                "name": m.get("name") or m["id"],
                "free": (
                    m.get("pricing", {}).get("prompt") == "0"
                    and m.get("pricing", {}).get("completion") == "0"
                ),
            }
            for m in raw
        ]
        _models_cache["all"] = all_models
        _models_cache["at"] = now
        return all_models
    except Exception:
        return _models_cache["all"] or []


def _native_provider_of(model: str, settings) -> str | None:
    if model == settings.OPENROUTER_MODEL or model == settings.OPENROUTER_CHEAP_MODEL:
        return "openrouter"
    if model == settings.OPENAI_MODEL or model == settings.OPENAI_CHEAP_MODEL:
        return "openai"
    if model == settings.ANTHROPIC_MODEL:
        return "anthropic"
    if model == settings.GEMINI_MODEL:
        return "gemini"
    if model == settings.BEDROCK_MODEL:
        return "bedrock"
    lowered = model.lower()
    if "/" in lowered or ":" in lowered:
        return "openrouter"
    return None


def _to_openrouter_slug(model: str) -> str | None:
    lowered = model.lower()
    if "/" in lowered or ":" in lowered:
        return None
    if lowered.startswith("gpt-"):
        return f"openai/{lowered}"
    if "claude" in lowered:
        return f"anthropic/{lowered}"
    if "gemini" in lowered:
        return f"google/{lowered}"
    if "deepseek" in lowered:
        return f"deepseek/{lowered}"
    return None


async def _resolve_selected_model(request: Request, selected: str) -> str | None:
    router = request.app.state.model_router
    settings = get_settings()
    available = set(await router.get_available_providers())
    provider_name = _native_provider_of(selected, settings)
    if provider_name in available:
        return selected
    if "openrouter" in available:
        slug = _to_openrouter_slug(selected)
        if slug:
            models = await _fetch_openrouter_models()
            if any(m["id"] == slug for m in models):
                return slug
    return None

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


class MemoryCreate(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    key: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source: str = "dashboard"
    importance: int = Field(default=5, ge=1, le=10)


@router.post("/memories")
async def create_memory(body: MemoryCreate):
    await save_memory(
        category=body.category,
        key=body.key,
        content=body.content,
        source=body.source,
        importance=body.importance,
    )
    return {"status": "saved"}


@router.get("/conversations")
async def list_conversations(conversation_id: str | None = None, limit: int = 50):
    return await get_conversation_logs(conversation_id, limit)


@router.get("/sessions")
async def list_sessions(limit: int = 50):
    return await list_sessions_db(limit=limit)


@router.delete("/sessions/{conversation_id}")
async def delete_conversation(conversation_id: str):
    await delete_session(conversation_id)
    return {"status": "deleted"}


class TitleRequest(BaseModel):
    title: str


def heuristic_title(logs: list[dict]) -> str:
    words: list[str] = []
    for log in logs:
        if log["role"] != "user":
            continue
        for word in log["content"].lower().replace("?", "").replace("!", "").split():
            cleaned = word.strip(".,;:\"'()[]")
            if cleaned in TITLE_FILLER_WORDS or not cleaned.isalpha():
                continue
            words.append(cleaned)
            if len(words) >= 5:
                break
        if len(words) >= 5:
            break
    if not words:
        return "Conversation"
    return " ".join(words).capitalize()


@router.put("/sessions/{conversation_id}/title")
async def rename_conversation(conversation_id: str, body: TitleRequest):
    title = body.title.strip()
    if not title:
        return {"status": "invalid", "title": ""}
    await set_conversation_title(conversation_id, title)
    return {"status": "renamed", "title": title}


@router.post("/sessions/{conversation_id}/title/auto")
async def auto_title_conversation(request: Request, conversation_id: str):
    logs = await get_conversation_logs(conversation_id, limit=50)
    title = None

    model_router = getattr(request.app.state, "model_router", None)
    if model_router is not None:
        transcript = "\n".join(
            f"{log['role'].upper()}: {log['content']}" for log in logs
        ) or "No messages yet."
        try:
            response = await model_router.complete(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a chat titling assistant. Given a conversation transcript, "
                            "reply with ONLY a short, descriptive title of at most 6 words. "
                            "No quotes, no punctuation at the end, no explanation."
                        ),
                    },
                    {"role": "user", "content": f"Transcript:\n{transcript}"},
                ],
                max_tokens=30,
                temperature=0.2,
            )
            if response.content:
                title = response.content.strip().strip('"').strip("'")
                title = " ".join(title.split())
        except Exception:
            title = None

    if not title:
        title = heuristic_title(logs)

    await set_conversation_title(conversation_id, title)
    return {"status": "renamed", "title": title}


@router.get("/tools")
async def list_tools():
    return {"tools": get_registered_tools()}


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    user_id: str = "dashboard"
    model: str | None = None


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    agent = request.app.state.agent
    try:
        model = body.model or None
        if model is None:
            model = await request.app.state.redis.get("dashboard:selected_model")
        result = await agent.process_message_detailed(
            user_message=body.message,
            conversation_id=body.conversation_id,
            channel="dashboard",
            user_id=body.user_id,
            model=model,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/models/selected")
async def get_selected_model(request: Request):
    model = await request.app.state.redis.get("dashboard:selected_model")
    return {"model": model}


class SelectedModelRequest(BaseModel):
    model: str | None = None


@router.put("/models/selected")
async def set_selected_model(request: Request, body: SelectedModelRequest):
    selected = (body.model or "").strip() or None
    resolved = None
    if selected is not None:
        resolved = await _resolve_selected_model(request, selected)
        if resolved is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Model '{selected}' is not available. "
                    "Choose a configured model or an OpenRouter model."
                ),
            )
    redis = request.app.state.redis
    if resolved is None:
        await redis.delete("dashboard:selected_model")
    else:
        await redis.set("dashboard:selected_model", resolved)
    return {"model": resolved}


@router.get("/models")
async def list_models(request: Request):
    settings = get_settings()
    router = request.app.state.model_router
    configured_entries = [
        (settings.OPENROUTER_MODEL, "OpenRouter (default)", "openrouter"),
        (settings.OPENROUTER_CHEAP_MODEL, "OpenRouter (cheap)", "openrouter"),
        (settings.OPENAI_MODEL, "OpenAI", "openai"),
        (settings.ANTHROPIC_MODEL, "Anthropic", "anthropic"),
        (settings.GEMINI_MODEL, "Gemini", "gemini"),
        (settings.BEDROCK_MODEL, "Bedrock", "bedrock"),
    ]
    available_names = set()
    for name, provider in router.providers.items():
        if await provider.is_available():
            available_names.add(name)
    configured = [
        {
            "id": model_id,
            "name": name,
            "available": provider_name in available_names,
        }
        for model_id, name, provider_name in configured_entries
    ]
    all_models = await _fetch_openrouter_models()
    free = [
        {"id": m["id"], "name": m["name"]}
        for m in all_models
        if m["free"]
    ]
    free.sort(key=lambda m: m["name"].lower())
    return {
        "free_models": free,
        "configured": configured,
    }
