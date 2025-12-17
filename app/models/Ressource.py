from datetime import time
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Column, JSON, Time, UniqueConstraint
from sqlalchemy.orm import validates
from sqlmodel import SQLModel, Field, Relationship

from app.models.Enum.EtatRessource import EtatRessource
from app.models.Enum.TypeRessource import TypeRessource

if TYPE_CHECKING:
    from app.models.Site import Site


class RessourceBase(SQLModel):
    nom: str = Field(min_length=3, index=True)
    type_ressource: TypeRessource
    capacite_maximum: int = Field(ge=1)
    description: str
    caracteristiques: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    site_id: int = Field(foreign_key="sites.id")
    localisation_batiment: str
    localisation_etage: str
    localisation_numero: str
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
    tarifs_horaires: Optional[float] = Field(default=None, ge=0)


class Ressource(RessourceBase, table=True):
    __tablename__ = "ressources"
    __table_args__ = (
        UniqueConstraint("nom", "site_id", name="unique_nom_site"),
    )

    id: Optional[int] = Field(primary_key=True, default=None)
    site: Optional["Site"] = Relationship(back_populates="ressources")

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
            "batiment": self.localisation_batiment,
            "etage": self.localisation_etage,
            "numero": self.localisation_numero
        }

    def set_localisation(self, batiment: str, etage: str, numero: str):
        self.localisation_batiment = batiment
        self.localisation_etage = etage
        self.localisation_numero = numero

    def est_ouverte(self, heure: time) -> bool:
        if self.type_ressource != TypeRessource.salle:
            return True

        if not self.horaires_ouverture or not self.horaires_fermeture:
            return True

        return self.horaires_ouverture <= heure <= self.horaires_fermeture

    def est_disponible(self) -> bool:
        return self.etat == EtatRessource.active


class RessourcePublic(RessourceBase):
    id: int


class RessourceCreate(RessourceBase):
    pass


class RessourceUpdate(SQLModel):
    capacite_maximum: Optional[int] = Field(default=None, ge=1)
    description: Optional[str] = None
    caracteristiques: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    site_id: Optional[int] = None
    localisation_batiment: Optional[str] = None
    localisation_etage: Optional[str] = None
    localisation_numero: Optional[str] = None
    etat: Optional[EtatRessource] = None
    horaires_ouverture: Optional[time] = Field(
        default=None,
        sa_column=Column(Time, nullable=True)
    )
    horaires_fermeture: Optional[time] = Field(
        default=None,
        sa_column=Column(Time, nullable=True)
    )
    images: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    tarifs_horaires: Optional[float] = Field(default=None, ge=0)


class RessourceListMeta(SQLModel):
    total: int
    offset: int
    limit: int
    returned: int
    sort_by: str
    sort_order: str


class RessourceListResponse(SQLModel):
    items: List[RessourcePublic]
    meta: RessourceListMeta