from fastapi import Request, HTTPException, status
from app.dependencies import get_current_user
from app.models.User import User
from app.models.Enum.TypeRole import TypeRole


def require_admin(request: Request) -> User:
    user = get_current_user(request)
    if user.role != TypeRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée aux administrateurs"
        )
    return user


def require_manager_or_admin(request: Request) -> User:
    user = get_current_user(request)
    if user.role not in [TypeRole.manager, TypeRole.admin]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée aux managers et administrateurs"
        )
    return user


def require_roles(allowed_roles: list[TypeRole]):
    def checker(request: Request) -> User:
        user = get_current_user(request)
        if user.role not in allowed_roles:
            roles_str = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôles autorisés: {roles_str}"
            )
        return user
    return checker


def require_authorization(authorization: str):
    def checker(request: Request) -> User:
        user = get_current_user(request)
        if authorization not in user.autorisations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Autorisation requise: {authorization}"
            )
        return user
    return checker


def check_user_can_access_resource(user: User, resource_user_id: int) -> bool:
    if user.role == TypeRole.admin:
        return True
    return user.id == resource_user_id
