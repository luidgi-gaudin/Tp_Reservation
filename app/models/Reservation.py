from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING, ClassVar

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import DateTime
from sqlalchemy.orm import validates

from app.models.Enum.StatutReservation import StatutReservation
from app.models.Enum.TypeRessource import TypeRessource

if TYPE_CHECKING:
    from app.models.Ressource import Ressource
    from app.models.User import User


class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"

    id: Optional[int] = Field(default=None, primary_key=True)

    ressource_id: int = Field(foreign_key="ressources.id")
    user_id: int = Field(foreign_key="users.id")
    createur_id: int = Field(foreign_key="users.id")

    ressource: Optional["Ressource"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Reservation.ressource_id]"}
    )
    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Reservation.user_id]"}
    )
    createur: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Reservation.createur_id]"}
    )

    # Dates
    debut: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    fin: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    date_creation: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True))
    )
    date_modification: datetime = Field(
        default_factory=datetime.now,
        sa_column=Column(DateTime(timezone=True))
    )

    statut: StatutReservation
    description: str
    nbr_participants: int = Field(gt=0, default=1)
    note: Optional[str] = Field(default=None)

    DUREE_MAX_PAR_TYPE: ClassVar[dict[TypeRessource, timedelta]] = {
        TypeRessource.salle: timedelta(hours=8),
        TypeRessource.vehicule: timedelta(hours=24),
        TypeRessource.equipement: timedelta(hours=8)
    }

    def _check_duree(self, debut_value: Optional[datetime], fin_value: Optional[datetime]) -> None:
        if not debut_value or not fin_value:
            return

        if fin_value <= debut_value:
            raise ValueError("La date de fin doit être postérieure à la date de début")

        duree = fin_value - debut_value

        if duree < timedelta(minutes=30):
            raise ValueError("La durée minimale d'une réservation est de 30 minutes")

        if hasattr(self, "ressource") and self.ressource:
            duree_max = self.DUREE_MAX_PAR_TYPE.get(
                self.ressource.type_ressource,
                timedelta(hours=8)
            )
            if duree > duree_max:
                raise ValueError(
                    f"La durée maximale pour une {self.ressource.type_ressource.value} "
                    f"est de {duree_max.total_seconds() / 3600:.0f} heures"
                )

    @validates("debut")
    def validate_debut(self, key, debut):
        if debut.minute not in [0, 15, 30, 45]:
            raise ValueError(
                f"L'heure de début doit être arrondie à 15 minutes "
                f"(minutes actuelles: {debut.minute})"
            )

        if debut < datetime.now():
            if not hasattr(self, "createur") or not self.createur or self.createur.role != "admin":
                raise ValueError(
                    "Impossible de créer une réservation dans le passé. "
                    "Seuls les administrateurs peuvent le faire."
                )

        # Vérifie la durée si fin est déjà renseignée
        fin_actuelle = getattr(self, "fin", None)
        self._check_duree(debut, fin_actuelle)

        return debut

    @validates("fin")
    def validate_fin(self, key, fin):
        if fin.minute not in [0, 15, 30, 45]:
            raise ValueError(
                f"L'heure de fin doit être arrondie à 15 minutes "
                f"(minutes actuelles: {fin.minute})"
            )

        debut_actuel = getattr(self, "debut", None)
        self._check_duree(debut_actuel, fin)

        return fin

    @validates("nbr_participants")
    def validate_capacite(self, key, nbr_participants):
        if hasattr(self, "ressource") and self.ressource:
            if nbr_participants > self.ressource.capacite_maximum:
                raise ValueError(
                    f"Le nombre de participants ({nbr_participants}) dépasse "
                    f"la capacité maximale de la ressource ({self.ressource.capacite_maximum})"
                )
        return nbr_participants

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
        self.date_modification = datetime.now()
        return True

    def confirmer(self):
        if self.statut != StatutReservation.en_cours:
            raise ValueError("Seules les réservations en attente peuvent être confirmées")

        self.statut = StatutReservation.confirme
        self.date_modification = datetime.now()

    def marquer_no_show(self):
        if datetime.now() < self.debut:
            raise ValueError("Impossible de marquer no-show avant la date de début")

        self.statut = StatutReservation.non_present
        self.date_modification = datetime.now()

    def terminer(self):
        if datetime.now() < self.fin:
            raise ValueError("Impossible de terminer une réservation avant sa date de fin")

        self.statut = StatutReservation.fini
        self.date_modification = datetime.now()

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