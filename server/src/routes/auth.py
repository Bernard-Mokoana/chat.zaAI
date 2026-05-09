from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.orm import Session

from src.utils.token import Token
from src.database.config.databaseConfig import get_db
from src.database.models.users import User
from src.schema.auth import LoginSchema
from src.services.auth_services import AuthService

import bcrypt

auth = APIRouter(prefix="/api/v1/auth", tags=["auth"])
auth_service = AuthService()

@auth.post("/login")
async def login(payload: LoginSchema, response: Response, request: Request, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not bcrypt.checkpw(payload.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    return auth_service.login(db=db, user=user, request=request, response=response)

@auth.post("/refresh")
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    return auth_service.refresh_access_token(db=db, request=request, response=response)