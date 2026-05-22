from datetime import datetime, timezone
from fastapi import HTTPException, status, Request, Response
from sqlalchemy.orm import Session
import bcrypt
import re

from src.database.models.users import User
from src.database.models.refresh_token import RefreshToken
from src.utils.token import Token

class AuthService:
    def __init__(self):
        self.token = Token()
        
    def register_user(self, db: Session, name: str, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        normalized_name = name.strip()

        if not normalized_name or not normalized_email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All fields are required",
            )
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, normalized_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )
        
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must at least be 8 characters long",
            )

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        new_user = User(
            name=normalized_name,
            email=normalized_email,
            password_hash=password_hash,
            tier="free",
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user
    
    def login(self, db: Session, user: User, request: Request, response: Response):

        user_payload = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
        }

        jti = self.token.create_jti()
        access_token = self.token.sign_access_token(user_payload)
        refresh_token = self.token.sign_refresh_token(user_payload, jti)

        self.token.persist_refresh_token(
            db=db,
            user=user_payload,
            refresh_token=refresh_token,
            jti=jti,
            request=request
        )

        self.token.set_refresh_cookie(response, refresh_token)

        return {"access_token": access_token, "token_type": "bearer", "user": user_payload}

    def refresh_access_token(self, db: Session, request: Request, response: Response):
        raw_refresh = request.cookies.get("refreshToken")

        if not raw_refresh:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
        
        try:
            payload = self.token.decode_refresh_token(raw_refresh)
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
        user_id = payload.get("id")
        jti = payload.get("jti")
        if not user_id or not jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed refresh token")
        
        token_hash = self.token.hash_token(raw_refresh)
        db_token = (
            db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.jwt_id == jti,
                RefreshToken.token == token_hash,
                RefreshToken.is_revoked.is_(False),
            )
            .first()
        )

        if not db_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not recognized")
        
        if db_token.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        user_payload = {"id": str(user.id), "email": user.email, "name": user.name}
        new_jti = self.token.create_jti()
        new_access = self.token.sign_access_token(user_payload)
        new_refresh = self.token.sign_refresh_token(user_payload, new_jti)

        replacement = self.token.persist_refresh_token(
            db=db,
            user=user_payload,
            refresh_token=new_refresh,
            jti=new_jti,
            request=request,
        )

        db_token.is_revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db_token.replaced_by = str(replacement.id)
        db.commit()

        new_user = { 
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
        }

        self.token.set_refresh_cookie(response, new_refresh)
        return { "access_token": new_access, "token_type": "bearer", "user": new_user}
    
    def logout(self, db: Session, request: Request, response: Response):
        raw_refresh = request.cookies.get("refreshToken")
        
        if raw_refresh:
            try:
                payload = self.token.decode_refresh_token(raw_refresh)
                user_id = payload.get("id")
                jti = payload.get("jti")
                token_hash = self.token.hash_token(raw_refresh)
                
                if user_id and jti:
                    db_token = (
                        db.query(RefreshToken)
                        .filter(
                            RefreshToken.user_id == user_id,
                            RefreshToken.jwt_id == jti,
                            RefreshToken.token == token_hash,
                            RefreshToken.is_revoked.is_(False),
                            )
                            .first()
                            )
                    
                    if db_token:
                        db_token.is_revoked = True
                        db_token.revoked_at = datetime.now(timezone.utc)
                        db.commit()
                        
            except Exception:
                pass
        
        self.token.clear_refresh_cookie(response)
        return {"message": "Logged out successfully"}