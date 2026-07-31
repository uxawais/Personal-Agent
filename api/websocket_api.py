import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from channels.webchat import WebChatChannel

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    webchat: WebChatChannel = websocket.app.state.webchat
    webchat.add_connection(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                content = msg.get("content", "")
                if content:
                    response = await webchat.handle_message(user_id, content)
                    await websocket.send_json({"type": "response", "content": response})
            except json.JSONDecodeError:
                response = await webchat.handle_message(user_id, data)
                await websocket.send_json({"type": "response", "content": response})
    except WebSocketDisconnect:
        webchat.remove_connection(user_id, websocket)
    except Exception:
        webchat.remove_connection(user_id, websocket)
