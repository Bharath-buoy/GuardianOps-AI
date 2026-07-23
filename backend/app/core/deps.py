"""
Auth dependency for protected routes.

Usage in a router:
    from app.core.deps import get_current_user

    @router.get("/secure-thing")
    async def secure_thing(user: dict = Depends(get_current_user)):
        ...
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.services.user_service import user_service

# tokenUrl is documentation-only (used by the Swagger "Authorize" button);
# the actual login endpoint lives at /api/auth/login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        payload = decode_access_token(token)
        email: str | None = payload.get("sub")
        if not email:
            raise credentials_error
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except jwt.PyJWTError:
        raise credentials_error

    user = await user_service.get_by_email(email)
    if not user:
        raise credentials_error
    return user
