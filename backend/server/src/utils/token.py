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

from backend.database.models.refresh_token import RefreshToken
from backend.database.models.reset_password_token import ResetPasswordToken
from backend.database.models.email_verification_token import EmailVerificationToken

load_dotenv()

REFRESH_TTL_SEC = 60 * 60 * 24 * 7
PASSWORD_RESET_TTL_SEC = 60 * 15
EMAIL_VERIFY_TTL_SEC = 60 * 60 * 24


class Token:
    def __init__(self):
        self.jwt_secret = os.environ.get("JWT_SECRET")
        self.expires_in = os.environ.get("EXPIRES_IN")
        self.refresh_jwt_secret = os.environ.get("REFRESH_JWT_SECRET")
        self.verify_jwt_secret = os.environ.get("VERIFY_JWT_SECRET")

        if not self.jwt_secret:
            raise ValueError("JWT_SECRET environment variable is required")
        if not self.expires_in:
            raise ValueError("EXPIRES_IN environment variable is required")
        if not self.refresh_jwt_secret:
            raise ValueError("REFRESH_JWT_SECRET environment variable is required")
        if not self.verify_jwt_secret:
            raise ValueError("VERIFY_JWT_SECRET environment variable is required")

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
    
    def sign_email_verification_token(self, user: dict, jti: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(seconds=EMAIL_VERIFY_TTL_SEC)
        payload = {
            "email": user.get("email"),
            "jti": jti,
            "exp": expire
        }
        return jwt.encode(payload, self.verify_jwt_secret, algorithm=self.algorithm) 

    def sign_forgot_password_token(self, user: dict, jti: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(seconds=PASSWORD_RESET_TTL_SEC)
        payload = {
            "email": user.get("email"),
            "jti": jti,
            "exp": expire
        }
        return jwt.encode(payload, self.verify_jwt_secret, algorithm=self.algorithm)

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
        
    def decode_email_verification_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.verify_jwt_secret, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification token expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification token")
        
    def decode_forgot_password_verification_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.verify_jwt_secret, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification token expired")
        except InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification token")

    def set_refresh_cookie(self, response: Response, refresh_token: str):
        is_prod = os.environ.get("APP_ENV") == "production"
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
        is_prod = os.environ.get('APP_ENV') == "production"
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
            token_hash=token_hash,
            jwt_id=jti,
            ip=ip,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        db.add(new_token)
        db.flush()
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
    
    def persist_reset_password_token(self, db: Session, user: dict, reset_token: str, jti: str, request: Optional[Request] = None):
        token_hash = self.hash_token(reset_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=PASSWORD_RESET_TTL_SEC)
        ip, user_agent = self._client_meta(request)

        user_id = user.get("id")
        if not user_id:
            raise ValueError("User id is required to persist password reset token")
        
        new_token = ResetPasswordToken(
            user_id=user_id,
            token_hash=token_hash,
            jwt_id=jti,
            ip=ip,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        db.add(new_token)
        db.flush()
        return new_token
    
    def invalidate_reset_password_tokens(self, db: Session, user_id: str) -> None:
        db.query(ResetPasswordToken).filter(
            ResetPasswordToken.user_id == user_id,
            ResetPasswordToken.is_used.is_(False),
        ).update(
            {"is_used": True, "used_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )

    def persist_email_verification_token(self, db: Session, user: dict, verification_token: str, jti: str, request: Optional[Request] = None): 
        token_hash = self.hash_token(verification_token)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=EMAIL_VERIFY_TTL_SEC)
        ip, user_agent = self._client_meta(request)

        user_id = user.get("id")
        if not user_id:
            raise ValueError("User_id is required to persist email verification token")
        
        new_token = EmailVerificationToken(
            user_id=user_id,
            token_hash=token_hash,
            jwt_id=jti,
            ip=ip,
            user_agent=user_agent,
            expires_at=expires_at,
        )

    def revoke_email_verification_tokens(self, db: Session, user_id: str) -> None:
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.is_revoked.is_(False),
            EmailVerificationToken.is_verified.is_(False),
        ).update(
            {"is_revoked": True, "revoked_at": datetime.now(timezone.utc)},
            synchronize_session=False,
        )

