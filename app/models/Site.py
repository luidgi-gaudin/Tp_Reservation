from datetime import time
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Column, Time
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.Ressource import Ressource


class Site(SQLModel, table=True):

    __tablename__ = "sites"

    id: Optional[int] = Field(primary_key=True, default=None)
    nom: str = Field(min_length=3)
    adresse: str
    ressources: List["Ressource"] = Relationship(back_populates="site")
    horaires_ouverture: time = Field(sa_column=Column(Time))
    horaires_fermeture: time = Field(sa_column=Column(Time))

    @validates('horaires_ouverture', 'horaires_fermeture')
    def verifier_horaires(self, key, value):
        if key == 'horaires_fermeture' and value:
            if hasattr(self, 'horaires_ouverture') and self.horaires_ouverture:
                if self.horaires_ouverture >= value:
                    raise ValueError("L'heure d'ouverture doit être avant l'heure de fermeture")
        return value