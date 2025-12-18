import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select
from fastapi import HTTPException, status

from app.models.User import User, UserCreate


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt, pwd_hash = hashed_password.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return new_hash.hex() == pwd_hash
    except:
        return False


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def register_user(session: Session, user_data: dict, password: str) -> User:
    existing_user = session.exec(
        select(User).where(User.email == user_data.get('email'))
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email déjà utilisé"
        )

    existing_username = session.exec(
        select(User).where(User.nom_utilisateur == user_data.get('nom_utilisateur'))
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom d'utilisateur déjà utilisé"
        )

    hashed_pwd = hash_password(password)

    user_data['hashed_password'] = hashed_pwd

    new_user = User(**user_data)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    user = session.exec(
        select(User).where(User.email == email)
    ).first()

    if not user:
        return None

    if not user.compte_actif:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


SESSIONS = {}


def create_session(user_id: int) -> str:
    token = create_session_token()
    SESSIONS[token] = {
        'user_id': user_id,
        'created_at': datetime.now(),
        'expires_at': datetime.now() + timedelta(hours=24)
    }
    return token


def get_session_user_id(token: str) -> Optional[int]:
    if token not in SESSIONS:
        return None

    session_data = SESSIONS[token]

    if datetime.now() > session_data['expires_at']:
        del SESSIONS[token]
        return None

    return session_data['user_id']


def delete_session(token: str):
    if token in SESSIONS:
        del SESSIONS[token]
