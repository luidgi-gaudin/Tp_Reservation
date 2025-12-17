from fastapi import Request, HTTPException, status
from app.models.User import User


def get_current_user(request: Request) -> User:
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    return request.state.user


def get_current_user_id(request: Request) -> int:
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    return request.state.user_id
