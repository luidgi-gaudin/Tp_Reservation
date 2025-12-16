from datetime import time
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from app.models.Enum.EtatRessource import EtatRessource
from app.models.Enum.TypeRessource import TypeRessource
from app.models.Localisation import Localisation


class Ressource (BaseModel):
    id: int = Field(gt=0)
    nom: str = Field(min_length=3)
    typeRessource: TypeRessource
    capaciteMaximum: int = Field(ge=1)
    description: str
    caracteristiques: Optional[List[str]] = Field(default=None)
    localisation: Localisation
    etat: EtatRessource
    horairesOuverture: Optional[time] = None
    horairesFermeture: Optional[time] = None
    images: List[str] = Field(default_factory=list)
    tarifsHoraires: float = Field(ge=0)

    @model_validator(mode='after')
    def verifier_horaires(self):
        # Les horaires sont UNIQUEMENT pour les salles
        if self.typeRessource == TypeRessource.salle:
            if self.horairesOuverture and self.horairesFermeture:
                if self.horairesOuverture >= self.horairesFermeture:
                    raise ValueError("L'heure d'ouverture doit être avant l'heure de fermeture")
        else:
            # Pour véhicules et équipements, pas d'horaires
            if self.horairesOuverture or self.horairesFermeture:
                raise ValueError(f"Les horaires ne sont pas applicables aux {self.typeRessource.value}")

        return self


