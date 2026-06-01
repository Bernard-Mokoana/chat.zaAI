from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from sqlalchemy.orm import Session

from src.utils.token import Token
from backend.database.config.databaseConfig import get_write_db
from backend.database.models.users import User
from src.schema.auth import LoginSchema, RegisterSchema
from src.services.auth_services import AuthService

import bcrypt

auth = APIRouter(prefix="/api/v1/auth", tags=["auth"])
auth_service = AuthService()

@auth.post("/register")
async def register(payload: RegisterSchema, response: Response, request: Request, db: Session = Depends(get_write_db)):
    user = auth_service.register_user(
        db=db,
        name=payload.name,
        email=payload.email,
        password=payload.password,
    )

    return auth_service.login(db=db, user=user, request=request, response=response)

@auth.post("/login")
async def login(payload: LoginSchema, response: Response, request: Request, db: Session = Depends(get_write_db)):

    normalized_email = payload.email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not bcrypt.checkpw(payload.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    return auth_service.login(db=db, user=user, request=request, response=response)

@auth.post("/refresh")
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_write_db)):
    return auth_service.refresh_access_token(db=db, request=request, response=response)

@auth.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_write_db)):
    return auth_service.logout(db=db, request=request, response=response)

    