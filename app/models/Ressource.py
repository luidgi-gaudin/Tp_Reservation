from datetime import time
from typing import Optional, List
from sqlalchemy import Column, JSON, Time
from sqlalchemy.orm import validates
from sqlmodel import SQLModel, Field, Relationship

from app.models.Enum.EtatRessource import EtatRessource
from app.models.Enum.TypeRessource import TypeRessource
from app.models.Site import Site


class Ressource(SQLModel, table=True):
    __tablename__ = "ressources"

    id: Optional[int] = Field(primary_key=True, default=None)
    nom: str = Field(min_length=3)
    type_ressource: TypeRessource
    capacite_maximum: int = Field(ge=1)
    description: str
    caracteristiques: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    site_id: int = Field(foreign_key="sites.id")
    site: Optional["Site"] = Relationship(back_populates="ressources")
    localisation_rue: str
    localisation_ville: str
    localisation_code_postal: int = Field(ge=10000, le=99999)
    localisation_pays: str = Field(default="France")

    etat: EtatRessource

    horaires_ouverture: Optional[time] = Field(
        default=None,
        sa_column=Column(Time, nullable=True)
    )
    horaires_fermeture: Optional[time] = Field(
        default=None,
        sa_column=Column(Time, nullable=True)
    )

    images: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )

    tarifs_horaires: float = Field(ge=0)

    @validates('horaires_ouverture', 'horaires_fermeture')
    def verifier_horaires(self, key, value):
        if key == 'horaires_fermeture' and value:
            if hasattr(self, 'horaires_ouverture') and self.horaires_ouverture:
                if self.horaires_ouverture >= value:
                    raise ValueError("L'heure d'ouverture doit être avant l'heure de fermeture")

        if hasattr(self, 'type_ressource'):
            if self.type_ressource != TypeRessource.salle and value is not None:
                raise ValueError(
                    f"Les horaires ne sont pas applicables aux {self.type_ressource.value}"
                )

        return value

    @property
    def localisation(self) -> dict:
        return {
            "rue": self.localisation_rue,
            "ville": self.localisation_ville,
            "code_postal": self.localisation_code_postal,
            "pays": self.localisation_pays
        }

    def set_localisation(self, rue: str, ville: str, code_postal: int, pays: str = "France"):
        if not 10000 <= code_postal <= 99999:
            raise ValueError("Code postal invalide")

        self.localisation_rue = rue
        self.localisation_ville = ville
        self.localisation_code_postal = code_postal
        self.localisation_pays = pays

    def est_ouverte(self, heure: time) -> bool:
        if self.type_ressource != TypeRessource.salle:
            return True

        if not self.horaires_ouverture or not self.horaires_fermeture:
            return True

        return self.horaires_ouverture <= heure <= self.horaires_fermeture

    def est_disponible(self) -> bool:
        return self.etat == EtatRessource.active