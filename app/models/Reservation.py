from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.Enum.StatutReservation import StatutReservation
from app.models.Enum.TypeRessource import TypeRessource
from app.models.Ressource import Ressource
from app.models.User import User


class Reservation(BaseModel):
    id: int = Field(ge=0)
    ressource: Ressource
    user: User
    debut: datetime
    fin: datetime
    statut: StatutReservation
    description: str
    nbrParticipants: int = Field(gt=0, default=1)
    note: Optional[str] = Field(default=None)
    dateCreation: datetime = Field(default_factory=datetime.now)
    dateModification: datetime = Field(default_factory=datetime.now)
    createur: User

    DUREE_MAX_PAR_TYPE = {
        TypeRessource.salle: timedelta(hours=8),
        TypeRessource.vehicule: timedelta(hours=24),
        TypeRessource.equipement: timedelta(hours=8)
    }

    @model_validator(mode='after')
    def verifier_date_modification(self):
        self.dateModification = datetime.now()
        return self

    @model_validator(mode='after')
    def verifier_duree_minimal_maximal(self):
        duree = self.fin - self.debut

        if duree < timedelta(minutes=30):
            raise ValueError("La durée minimale d'une réservation est de 30 minutes")

        duree_max = self.DUREE_MAX_PAR_TYPE.get(
            self.ressource.typeRessource,
            timedelta(hours=8)
        )

        if duree > duree_max:
            raise ValueError(
                f"La durée maximale pour une {self.ressource.typeRessource.value} "
                f"est de {duree_max.total_seconds() / 3600:.0f} heures"
            )

        return self

    @model_validator(mode='after')
    def verifier_fin_posterieure_debut(self):
        if self.fin <= self.debut:
            raise ValueError("La date de fin doit être postérieure à la date de début")
        return self

    @model_validator(mode='after')
    def verifier_reservation_passee(self):
        if self.debut < datetime.now():
            if self.createur.role != "admin":
                raise ValueError(
                    "Impossible de créer une réservation dans le passé. "
                    "Seuls les administrateurs peuvent le faire."
                )
        return self

    @model_validator(mode='after')
    def verifier_creneaux_arrondis(self):
        if self.debut.minute not in [0, 15, 30, 45]:
            raise ValueError(
                f"L'heure de début doit être arrondie à 15 minutes "
                f"(minutes actuelles: {self.debut.minute})"
            )

        if self.fin.minute not in [0, 15, 30, 45]:
            raise ValueError(
                f"L'heure de fin doit être arrondie à 15 minutes "
                f"(minutes actuelles: {self.fin.minute})"
            )

        return self

    @model_validator(mode='after')
    def verifier_capacite_ressource(self):
        if self.nbrParticipants > self.ressource.capaciteMaximum:
            raise ValueError(
                f"Le nombre de participants ({self.nbrParticipants}) dépasse "
                f"la capacité maximale de la ressource ({self.ressource.capaciteMaximum})"
            )
        return self

    def peut_etre_annulee(self) -> bool:
        delai_minimum = timedelta(hours=2)
        temps_avant_debut = self.debut - datetime.now()
        return temps_avant_debut >= delai_minimum

    def annuler(self) -> bool:
        if not self.peut_etre_annulee():
            raise ValueError(
                "Impossible d'annuler : la réservation commence dans moins de 2 heures"
            )

        if self.statut in [StatutReservation.annule, StatutReservation.fini]:
            raise ValueError(f"Impossible d'annuler une réservation avec le statut {self.statut.value}")

        self.statut = StatutReservation.annule
        self.dateModification = datetime.now()
        return True

    def confirmer(self):
        if self.statut != StatutReservation.en_cours:
            raise ValueError("Seules les réservations en attente peuvent être confirmées")

        self.statut = StatutReservation.confirme
        self.dateModification = datetime.now()

    def marquer_no_show(self):
        if datetime.now() < self.debut:
            raise ValueError("Impossible de marquer no-show avant la date de début")

        self.statut = StatutReservation.non_present
        self.dateModification = datetime.now()

    def terminer(self):
        if datetime.now() < self.fin:
            raise ValueError("Impossible de terminer une réservation avant sa date de fin")

        self.statut = StatutReservation.fini
        self.dateModification = datetime.now()

    @property
    def duree_minutes(self) -> int:
        return int((self.fin - self.debut).total_seconds() / 60)

    @property
    def est_active(self) -> bool:
        maintenant = datetime.now()
        return (
                self.debut <= maintenant <= self.fin
                and self.statut == StatutReservation.confirme
        )

    @property
    def est_a_venir(self) -> bool:
        return (
                self.debut > datetime.now()
                and self.statut in [StatutReservation.en_cours, StatutReservation.confirme]
        )