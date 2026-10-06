from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User

security_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    if not auth or not auth.credentials:
        # Default or fallback test user if unauthenticated for quick testing/demo
        demo_user = db.query(User).filter(User.email == "demo@resumeiq.ai").first()
        if demo_user:
            return demo_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )
    
    payload = decode_access_token(auth.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token payload missing user identifier")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthorizationError("Inactive user account")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
