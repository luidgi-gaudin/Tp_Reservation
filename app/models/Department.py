from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy.orm import validates
from app.models.Site import Site
from app.models.User import User


class Department(SQLModel, table=True):
    __tablename__ = "departments"

    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(min_length=3)
    site: Site = Field(foreign_key="sites.id")
    manager: User = Field(foreign_key="users.id")
    budgetAnnuel: Optional[float] = Field(ge=0)

    @validates("manager")
    def user_must_be_manager(cls, manager: User) -> User:
        if manager.role not in ["manager", "admin"]:
            raise ValueError(f"L'utilisateur sélectionné doit etre manager ou admin !  (role actuel: {manager.role})")
        return manager
