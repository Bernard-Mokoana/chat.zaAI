import logging
import bcrypt
import re

from datetime import datetime, timezone
from fastapi import HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from backend.database.models.users import User
from backend.database.models.refresh_token import RefreshToken
from backend.database.models.reset_password_token import ResetPasswordToken
from backend.database.models.email_verification_token import EmailVerificationToken
from backend.database.models.tiers import Tier as TierModel

from backend.server.src.schema.auth import LoginSchema

from backend.server.src.utils.token import Token

from backend.server.src.utils.emailUtils import send_email_verification, send_password_reset_email

logger = logging.getLogger()
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

        tier_obj = db.query(TierModel).filter(TierModel.name == "free").first()
        if not tier_obj:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="System configuration error: free tier not found")
        
        new_user = User(
            name=normalized_name,
            email=normalized_email,
            password_hash=password_hash,
            tier_id=tier_obj.id,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        jti = self.token.create_jti()
        verification_token = self.token.sign_email_verification_token(
            {"email": normalized_email},
            jti,
        )

        self.token.persist_email_verification_token(
            db=db,
            user={"id": str(new_user.id)},
            verification_token=verification_token,
            jti=jti,
            # request=request,
        )
        db.commit()
        
        send_email_verification(normalized_email, verification_token)

        return new_user
    
    def authenticate_user(self, db: Session, email: str, password: str) -> User:
          normalized_email = email.strip().lower()
          
          user = db.query(User).filter(User.email == normalized_email).first()
          
          if not user:
              raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
          
          if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
              raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
          
          return user

    def login(self, db: Session, user: User, request: Request, response: Response):

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your inbox."
            )

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
        db.commit()

        self.token.set_refresh_cookie(response, refresh_token)

        return {"access_token": access_token, "token_type": "Bearer", "user": user_payload}
    
    def verify_email_token(self, db: Session, token_str: str):
       
        payload = self.token.decode_email_verification_token(token_str)

        email = payload.get("email")
        jti = payload.get("jti")
        if not email or not jti:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed token payload")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        token_hash = self.token.hash_token(token_str)
        db_token = (
            db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.jwt_id == jti,
                EmailVerificationToken.token_hash == token_hash
            )
            .first()
        )

        if not db_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification token not recognized")
        
        if db_token.is_revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification token has been revoked")
        
        if db_token.is_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Token already used")
        
        if db_token.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verification token expired")
        
        user.is_verified = True
        db_token.is_verified = True
        db_token.revoked_at = datetime.now(timezone.utc)
        db.commit()

        return {"message": "Email verified successfully"}
        
    def request_password_reset(self, db: Session, email: str):
        normalized_email = email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()

        if not user:
            return {"message": "If the email exists, a password reset link has been sent"}
        
        self.token.invalidate_reset_password_tokens(db, user.id)
        
        jti = self.token.create_jti()
        reset_token = self.token.sign_forgot_password_token({"email": normalized_email}, jti)

        self.token.persist_reset_password_token(
            db=db,
            user={"id": str(user.id)},
            reset_token=reset_token,
            jti=jti,
        )
        db.commit()

        send_password_reset_email(normalized_email, reset_token)

        return {"message": "If the email exists, a password reset link has been sent."}
    
    def reset_password(self, db: Session, token_str: str, new_password: str):
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Password must at least be 8 characters long"
            )
        
        payload = self.token.decode_forgot_password_verification_token(token_str)
   
        email = payload.get("email")
        jti = payload.get("jti")
        if not email or not jti:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed token payload")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        token_hash = self.token.hash_token(token_str)
        db_token = (
            db.query(ResetPasswordToken).filter(
                ResetPasswordToken.user_id == user.id,
                ResetPasswordToken.jwt_id == jti,
                ResetPasswordToken.token_hash == token_hash,
                ResetPasswordToken.is_used.is_(False),
            )
            .first()
        )

        if not db_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Reset token not recognized")
        
        if db_token.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Reset token expired")
        
        password_hash = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user.password_hash = password_hash
        db_token.is_used = True
        db_token.used_at = datetime.now(timezone.utc)
        db.commit()

        return {"message": "Password reset successfully"}
        
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
                RefreshToken.token_hash == token_hash,
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
        return { "access_token": new_access, "token_type": "Bearer", "user": new_user}
    
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
                            RefreshToken.token_hash == token_hash,
                            RefreshToken.is_revoked.is_(False),
                            )
                            .first()
                            )
                    
                    if db_token:
                        db_token.is_revoked = True
                        db_token.revoked_at = datetime.now(timezone.utc)
                        db.commit()
                        
            except Exception:
                logger.warning("Failed to revoke refresh token during logout", exc_info=True)
        
        self.token.clear_refresh_cookie(response)
        return {"message": "Logged out successfully"}