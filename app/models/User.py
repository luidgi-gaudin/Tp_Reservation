from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, JSON, DateTime
from sqlmodel import SQLModel, Field, Relationship

from app.models.Department import Department
from app.models.Enum.TypePriorite import TypePriorite
from app.models.Enum.TypeRole import TypeRole
from app.models.Reservation import Reservation


class User(SQLModel, table=True):

    __tablename__ = "users"

    id: Optional[int] = Field(primary_key=True, default=None)
    nom_utilisateur: str = Field(min_length=3)
    email: str = Field(unique=True)
    nom_prenom: str = Field(min_length=3)
    role: TypeRole

    department_id: Optional[int] = Field(default=None, foreign_key="departments.id")

    department: Optional["Department"] = Relationship(back_populates="users")

    autorisations: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )

    priorite: TypePriorite
    compte_actif: bool = Field(default=True)

    date_creation: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True))
    )

    reservations_faites: List["Reservation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Reservation.user_id]"}
    )

    reservations_creees: List["Reservation"] = Relationship(
        back_populates="createur",
        sa_relationship_kwargs={"foreign_keys": "[Reservation.createur_id]"}
    )