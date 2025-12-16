from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import validates

from app.models.Enum.TypeRole import TypeRole

if TYPE_CHECKING:
    from app.models.Site import Site
    from app.models.User import User


class Department(SQLModel, table=True):
    __tablename__ = "departments"

    id: Optional[int] = Field(default=None, primary_key=True)
    nom: str = Field(min_length=3)

    site_id: int = Field(foreign_key="sites.id")
    site: Optional["Site"] = Relationship()

    manager_id: int = Field(foreign_key="users.id")
    manager: Optional["User"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[Department.manager_id]"})

    users: List["User"] = Relationship(back_populates="department")

    budgetAnnuel: Optional[float] = Field(ge=0)

    @validates("manager")
    def user_must_be_manager(self, key, manager: Optional["User"]):
        if manager is None:
            return manager

        if manager.role not in (TypeRole.manager, TypeRole.admin):
            raise ValueError(
                f"L'utilisateur sélectionné doit être manager ou admin ! (role actuel: {manager.role})"
            )
        return manager