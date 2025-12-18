from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlmodel import Session

from app.helpers.auth.auth import get_session_user_id
from app.database.database import engine
from app.models.User import User


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public_paths = [
            "/docs",
            "/openapi.json",
            "/redoc",
            "/auth/register",
            "/auth/login",
        ]

        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        token = request.cookies.get("session_token")
        if not token:
            token = request.headers.get("Authorization")
            if token and token.startswith("Bearer "):
                token = token[7:]

        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Non authentifié"}
            )

        user_id = get_session_user_id(token)
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Session invalide ou expirée"}
            )

        with Session(engine) as session:
            user = session.get(User, user_id)
            if not user or not user.compte_actif:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Utilisateur non trouvé ou désactivé"}
                )

            request.state.user = user
            request.state.user_id = user_id

        response = await call_next(request)
        return response
