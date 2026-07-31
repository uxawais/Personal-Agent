from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse
from agent.config import get_settings

router = APIRouter()


@router.post("/slack/events")
async def slack_events(request: Request):
    app = request.app
    slack = app.state.slack
    if not slack:
        return PlainTextResponse("Slack not configured", status_code=503)
    return await slack.handler.handle(request)


@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    app = request.app
    whatsapp = app.state.whatsapp
    if not whatsapp:
        return PlainTextResponse("WhatsApp not configured", status_code=503)
    payload = await request.json()
    await whatsapp.handle_webhook(payload)
    return {"status": "ok"}
