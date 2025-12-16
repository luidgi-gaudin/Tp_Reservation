from typing import Optional

from pydantic import BaseModel, Field, field_validator
from app.models.Site import Site
from app.models.User import User


class Department(BaseModel):
    nom: str = Field(min_length=3)
    site: Site
    manager: User
    budgetAnnuel: Optional[float] = Field(ge=0)

    @field_validator("manager")
    def user_must_be_manager(cls, manager: User) -> User:
        if manager.role not in ["manager", "admin"]:
            raise ValueError(f"L'utilisateur sélectionné doit etre manager ou admin !  (role actuel: {manager.role})")
        return manager
