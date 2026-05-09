from datetime import datetime, timezone
from fastapi import HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from src.database.models.users import User
from src.database.models.refresh_token import RefreshToken
from src.utils.token import Token

class AuthService:
    def __init__(self):
        self.token = Token()


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

        return {"access_token": access_token, "token_type": "bearer"}
    
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
        if not user_id or not ti:
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
        
        db_token.is_revoked = True
        db_token.revoked_at = datetime.now(timezone.utc)

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
        db_token.replaced_by = str(replacement.id)
        db.commit()

        self.token.set_refresh_cookie(response, new_refresh)
        return { "access_token": new_access, "token_type": "bearer"}
        
    
