from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.database.config.databaseConfig import get_db
from src.database.models.users import User
from src.utils.token import Token

bearer = HTTPBearer(auto_error=False)
token_util = Token()

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer),
        db: Session = Depends(get_db)) -> User:
        
        if not credentials:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorisation header")
        
        if credentials.scheme.lower() != "bearer":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
        
        try:
                payload = token_util.decode_access_token(credentials.credentials)
        except (ValueError, KeyError, TypeError) as e:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        user_id = payload.get("id")
        if not user_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        return user
