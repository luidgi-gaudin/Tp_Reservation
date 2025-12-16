from datetime import time

from pydantic import BaseModel, Field

from app.models.Localisation import Localisation
from app.models.Ressource import Ressource


class Site(BaseModel):
    nom: str = Field(min_length=3)
    adresse: Localisation
    ressources: list[Ressource] = Field(default_factory=list)
    horairesOuverture: time
    horairesFermeture: time