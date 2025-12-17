from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime
from sqlalchemy.orm import validates

from app.models.Enum.TypeDisponibilite import TypeDisponibilite
from app.models.Enum.Recurrence import Recurrence

if TYPE_CHECKING:
    from app.models.Ressource import Ressource


class ResourceAvailabilityBase(SQLModel):
    ressource_id: int = Field(foreign_key="ressources.id")
    type_disponibilite: TypeDisponibilite
    debut: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    fin: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    raison_indisponibilite: Optional[str] = Field(default=None)
    recurrence: Recurrence = Field(default=Recurrence.ponctuel)


class ResourceAvailability(ResourceAvailabilityBase, table=True):
    __tablename__ = "resource_availabilities"

    id: Optional[int] = Field(default=None, primary_key=True)

    ressource: Optional["Ressource"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ResourceAvailability.ressource_id]"}
    )

    date_creation: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True))
    )

    @validates("debut", "fin")
    def validate_dates(self, key, value):
        if key == "fin" and value:
            debut_actuel = getattr(self, "debut", None)
            if debut_actuel and value <= debut_actuel:
                raise ValueError("La date de fin doit être postérieure à la date de début")
        return value


class ResourceAvailabilityPublic(ResourceAvailabilityBase):
    id: int
    date_creation: datetime


class ResourceAvailabilityCreate(ResourceAvailabilityBase):
    pass


class ResourceAvailabilityUpdate(SQLModel):
    ressource_id: Optional[int] = None
    type_disponibilite: Optional[TypeDisponibilite] = None
    debut: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    fin: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    raison_indisponibilite: Optional[str] = None
    recurrence: Optional[Recurrence] = None
