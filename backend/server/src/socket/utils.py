from typing import Optional
from backend.server.src.utils.token import Token

token_util = Token()

async def validate_token(token: Optional[str]) -> dict:
    if token is None or token == "":
        raise ValueError("Missing token")

    try:
        payload = token_util.decode_access_token(token)
    except Exception as e:
        raise ValueError(f"Invalid token: {str(e)}")

    if not payload.get("id"):
        raise ValueError("Invalid token payload - missing id")

    return payload
