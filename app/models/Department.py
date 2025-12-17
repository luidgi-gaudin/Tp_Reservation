from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import validates

from app.models.Enum.TypeRole import TypeRole

if TYPE_CHECKING:
    from app.models.Site import Site
    from app.models.User import User


class DepartmentBase(SQLModel):
    nom: str = Field(min_length=3, index=True)
    site_id: int = Field(foreign_key="sites.id")
    manager_id: int = Field(foreign_key="users.id")
    budgetAnnuel: Optional[float] = Field(default=None, ge=0)


class Department(DepartmentBase, table=True):
    __tablename__ = "departments"

    id: Optional[int] = Field(default=None, primary_key=True)

    site: Optional["Site"] = Relationship()
    manager: Optional["User"] = Relationship(sa_relationship_kwargs={"foreign_keys": "[Department.manager_id]"})
    users: List["User"] = Relationship(back_populates="department")

    @validates("manager")
    def user_must_be_manager(self, key, manager: Optional["User"]):
        if manager is None:
            return manager

        if manager.role not in (TypeRole.manager, TypeRole.admin):
            raise ValueError(
                f"L'utilisateur sélectionné doit être manager ou admin ! (role actuel: {manager.role})"
            )
        return manager


class DepartmentPublic(DepartmentBase):
    id: int


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(SQLModel):
    nom: Optional[str] = Field(default=None, min_length=3)
    site_id: Optional[int] = None
    manager_id: Optional[int] = None
    budgetAnnuel: Optional[float] = Field(default=None, ge=0)