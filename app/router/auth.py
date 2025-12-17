from fastapi import APIRouter, HTTPException, status, Response, Request
from sqlmodel import SQLModel
from typing import Optional

from app.database import SessionDep
from app.auth import register_user, authenticate_user, create_session, delete_session
from app.models.User import UserPublic
from app.models.Enum.TypeRole import TypeRole
from app.models.Enum.TypePriorite import TypePriorite
from app.dependencies import get_current_user


auth_router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(SQLModel):
    nom_utilisateur: str
    email: str
    nom_prenom: str
    password: str
    role: TypeRole
    priorite: TypePriorite
    site_principal_id: int
    department_id: Optional[int] = None


class LoginRequest(SQLModel):
    email: str
    password: str


class AuthResponse(SQLModel):
    message: str
    user: UserPublic
    token: str


@auth_router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, response: Response, session: SessionDep):
    password = request.password
    user_data = request.model_dump(exclude={'password'})

    user = register_user(session, user_data, password)

    token = create_session(user.id)

    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    return AuthResponse(
        message="Inscription réussie",
        user=UserPublic.model_validate(user),
        token=token
    )


@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, response: Response, session: SessionDep):
    user = authenticate_user(session, request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    token = create_session(user.id)

    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )

    return AuthResponse(
        message="Connexion réussie",
        user=UserPublic.model_validate(user),
        token=token
    )


@auth_router.post("/logout")
def logout(response: Response):
    response.delete_cookie("session_token")
    return {"message": "Déconnexion réussie"}


@auth_router.get("/me", response_model=UserPublic)
def get_me(request: Request):
    user = get_current_user(request)
    return UserPublic.model_validate(user)