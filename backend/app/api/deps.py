from typing import Generator, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User

security_bearer = HTTPBearer(auto_error=False)

def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = decode_access_token(auth.credentials, expected_type="access")
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user identifier",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Enforce scope: extension tokens are limited strictly to extension endpoints
    scope = payload.get("scope", "web")
    path = request.url.path
    if scope == "extension" and not path.startswith("/api/v1/extension"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: extension tokens are restricted to extension endpoints"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
