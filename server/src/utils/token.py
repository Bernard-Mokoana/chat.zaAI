import os
import hashlib
import secrets
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Response, Request, HTTPException, status
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from src.database.models.refresh_token import RefreshToken

load_dotenv()

REFRESH_TTL_SEC = 60 * 60 * 24 * 7


class Token:
    def __init__(self):
        self.jwt_secret = os.environ.get("JWT_SECRET")
        self.expires_in = os.environ.get("EXPIRES_IN")
        self.refresh_jwt_secret = os.environ.get("REFRESH_JWT_SECRET")

        if not self.jwt_secret:
            raise ValueError("JWT_SECRET environment variable is required")
        if not self.expires_in:
            raise ValueError("EXPIRES_IN environment variable is required")
        if not self.refresh_jwt_secret:
            raise ValueError("REFRESH_JWT_SECRET environment variable is required")

        self.algorithm = "HS256"

    def hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def create_jti(self) -> str:
        return secrets.token_hex(16)

    def sign_access_token(self, user: dict) -> str:
        try:
            if self.expires_in.endswith("h"):
                minutes = int(self.expires_in[:-1]) * 60
            else:
                minutes = int(self.expires_in)
        except (AttributeError, ValueError) as e:
            raise ValueError(f"Invalid EXPIRES_IN format: {self.expires_in}") from e

        expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        payload = {
            "id": user.get("id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "exp": expire,
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.algorithm)

    def sign_refresh_token(self, user: dict, jti: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TTL_SEC)
        payload = {
            "id": user.get("id"),
            "jti": jti,
            "exp": expire,
        }
        return jwt.encode(payload, self.refresh_jwt_secret, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

    def decode_refresh_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.refresh_jwt_secret, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    def set_refresh_cookie(self, response: Response, refresh_token: str):
        is_prod = os.environ.get("NODE_ENV") == "production"
        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            httponly=True,
            secure=is_prod,
            samesite="lax",
            path="/api/v1/auth",
            max_age=REFRESH_TTL_SEC,
        )

    def clear_refresh_cookie(self, response: Response):
        is_prod = os.environ.get('NODE_ENV') == "production"
        response.delete_cookie(
            key="refreshToken",
            httponly=True,
            secure=is_prod,
            samesite="lax",
            path="/api/v1/auth",
        )

    def _client_meta(self, request: Optional[Request]) -> tuple[Optional[str], Optional[str]]:
        if not request:
            return None, None
        forwarded = request.headers.get("x-forwarded-for")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)
        user_agent = request.headers.get("user-agent")
        return ip, user_agent

    def persist_refresh_token(self, db: Session, user: dict, refresh_token: str, jti: str, request: Optional[Request] = None):
        token_hash = self.hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TTL_SEC)
        ip, user_agent = self._client_meta(request)

        user_id = user.get("id")
        if not user_id:
            raise ValueError("User id is required to persist refresh token")

        new_token = RefreshToken(
            user_id=user_id,
            token=token_hash,
            jwt_id=jti,
            ip=ip,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        return new_token

    def rotate_refresh_token(self, db: Session, user: dict, request: Optional[Request], response: Optional[Response]) -> str:

        new_jti = self.create_jti()
        new_access = self.sign_access_token(user)
        new_refresh = self.sign_refresh_token(user, new_jti)

        self.persist_refresh_token(
            db=db,
            user=user,
            refresh_token=new_refresh,
            jti=new_jti,
            request=request
        )

        if response:
            self.set_refresh_cookie(response, new_refresh)

        return new_access   