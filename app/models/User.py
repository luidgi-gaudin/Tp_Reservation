from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Column, JSON, DateTime
from sqlmodel import SQLModel, Field, Relationship

from app.models.Enum.TypePriorite import TypePriorite
from app.models.Enum.TypeRole import TypeRole

if TYPE_CHECKING:
    from app.models.Department import Department
    from app.models.Reservation import Reservation
    from app.models.Site import Site


class UserBase(SQLModel):
    nom_utilisateur: str = Field(min_length=3, index=True)
    email: str = Field(unique=True, index=True)
    nom_prenom: str = Field(min_length=3)
    role: TypeRole
    autorisations: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )
    priorite: TypePriorite
    compte_actif: bool = Field(default=True)
    site_principal_id: int = Field(foreign_key="sites.id")


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(primary_key=True, default=None)

    date_creation: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True))
    )

    site_principal: Optional["Site"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[User.site_principal_id]"}
    )

    department: Optional["Department"] = Relationship(back_populates="users")

    reservations_faites: List["Reservation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Reservation.user_id]"}
    )

    reservations_creees: List["Reservation"] = Relationship(
        back_populates="createur",
        sa_relationship_kwargs={"foreign_keys": "[Reservation.createur_id]"}
    )


class UserPublic(UserBase):
    id: int
    date_creation: datetime


class UserCreate(UserBase):
    pass


class UserUpdate(SQLModel):
    nom_utilisateur: Optional[str] = Field(default=None, min_length=3)
    email: Optional[str] = None
    nom_prenom: Optional[str] = Field(default=None, min_length=3)
    role: Optional[TypeRole] = None
    autorisations: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    priorite: Optional[TypePriorite] = None
    compte_actif: Optional[bool] = None
    site_principal_id: Optional[int] = None