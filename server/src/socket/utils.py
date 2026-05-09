from fastapi import WebSocket, status, Query
from typing import Optional
from src.utils.token import Token

token_util = Token()

async def get_token(websocket: WebSocket, token: Optional[str] = Query(None)):
    if token is None or token == "":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = token_util.decode_access_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not payload.get("id"):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    return payload
