"""Authentication endpoints - single-user register/login with JWT."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.models.user import TokenResponse, UserLogin, UserPublic, UserRegister
from app.services.user_service import user_service

logger = logging.getLogger("guardianops.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _to_public(user: dict) -> UserPublic:
    return UserPublic(
        user_id=user["user_id"],
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    """
    Register the (single) GuardianOps AI operator account.

    GuardianOps AI is single-user by design — this endpoint returns 409 if
    an account has already been created.
    """
    try:
        user = await user_service.register(payload.name, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    logger.info("New GuardianOps AI operator account registered: %s", user["email"])
    token = create_access_token(subject=user["email"])
    return TokenResponse(access_token=token, user=_to_public(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    user = await user_service.authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    token = create_access_token(subject=user["email"])
    return TokenResponse(access_token=token, user=_to_public(user))


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: dict = Depends(get_current_user)):
    return _to_public(current_user)


@router.get("/status")
async def registration_status():
    """Lets the frontend decide whether to show Register or redirect to Login."""
    exists = await user_service.user_exists()
    return {"account_exists": exists}
