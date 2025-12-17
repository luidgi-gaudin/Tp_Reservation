from typing import Optional, Literal
from datetime import datetime, timedelta

from sqlmodel import select
from sqlalchemy import func, and_

from app.models.Ressource import Ressource, RessourceStatistics, DisponibiliteJour
from app.models.Reservation import Reservation, ReservationPublicSimple
from app.models.ResourceAvailability import ResourceAvailability
from app.models.Enum.TypeRessource import TypeRessource
from app.models.Enum.EtatRessource import EtatRessource
from app.models.Enum.StatutReservation import StatutReservation
from app.models.Enum.TypeDisponibilite import TypeDisponibilite


def ressource_list(
    session,
    *,
    offset: int = 0,
    limit: int = 100,
    type_of_ressource: Optional[TypeRessource] = None,
    site_id: Optional[int] = None,
    batiment: Optional[str] = None,
    disponible: Optional[bool] = None,
    caracteristiques: Optional[str] = None,
    minimum_capacity: int = 0,
    sort_by: Literal["nom", "capacite", "type"] = "nom",
    sort_order: Literal["asc", "desc"] = "asc",
) -> dict:
    conditions = []

    if type_of_ressource is not None:
        conditions.append(Ressource.type_ressource == type_of_ressource)

    if site_id is not None:
        conditions.append(Ressource.site_id == site_id)

    if batiment:
        conditions.append(Ressource.localisation_batiment.ilike(f"%{batiment}%"))

    if disponible is True:
        conditions.append(Ressource.etat == EtatRessource.active)
    elif disponible is False:
        conditions.append(Ressource.etat != EtatRessource.active)

    if minimum_capacity > 0:
        conditions.append(Ressource.capacite_maximum >= minimum_capacity)

    if caracteristiques:
        requested = [c.strip() for c in caracteristiques.split(",") if c.strip()]
        for c in requested:
            conditions.append(Ressource.caracteristiques.contains(c))

    sort_map = {
        "nom": Ressource.nom,
        "capacite": Ressource.capacite_maximum,
        "type": Ressource.type_ressource,
    }
    order_col = sort_map[sort_by]
    order_col = order_col.desc() if sort_order == "desc" else order_col.asc()

    total_stmt = select(func.count()).select_from(Ressource)
    if conditions:
        total_stmt = total_stmt.where(*conditions)
    total = session.exec(total_stmt).one()

    stmt = select(Ressource)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(order_col).offset(offset).limit(limit)

    items = session.exec(stmt).all()

    return {
        "items": items,
        "meta": {
            "total": total,
            "offset": offset,
            "limit": limit,
            "returned": len(items),
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    }


def get_ressource_statistics(session, ressource_id: int) -> RessourceStatistics:
    now = datetime.now()

    total_reservations = session.exec(
        select(func.count())
        .select_from(Reservation)
        .where(Reservation.ressource_id == ressource_id)
    ).one()

    reservations_actives = session.exec(
        select(func.count())
        .select_from(Reservation)
        .where(
            and_(
                Reservation.ressource_id == ressource_id,
                Reservation.debut <= now,
                Reservation.fin >= now,
                Reservation.statut == StatutReservation.confirme
            )
        )
    ).one()

    reservations_a_venir = session.exec(
        select(func.count())
        .select_from(Reservation)
        .where(
            and_(
                Reservation.ressource_id == ressource_id,
                Reservation.debut > now,
                Reservation.statut.in_([StatutReservation.en_cours, StatutReservation.confirme])
            )
        )
    ).one()

    date_30_jours = now - timedelta(days=30)
    reservations_30j = session.exec(
        select(Reservation)
        .where(
            and_(
                Reservation.ressource_id == ressource_id,
                Reservation.debut >= date_30_jours,
                Reservation.statut.in_([StatutReservation.confirme, StatutReservation.fini])
            )
        )
    ).all()

    heures_reservees_30_jours = sum(
        (r.fin - r.debut).total_seconds() / 3600 for r in reservations_30j
    )

    if total_reservations > 0:
        all_reservations = session.exec(
            select(Reservation)
            .where(Reservation.ressource_id == ressource_id)
        ).all()
        durees = [(r.fin - r.debut).total_seconds() / 60 for r in all_reservations]
        reservation_moyenne_duree = sum(durees) / len(durees) if durees else 0
    else:
        reservation_moyenne_duree = 0

    date_7_jours = now + timedelta(days=7)
    reservations_7j = session.exec(
        select(Reservation)
        .where(
            and_(
                Reservation.ressource_id == ressource_id,
                Reservation.debut >= now,
                Reservation.debut < date_7_jours,
                Reservation.statut.in_([StatutReservation.en_cours, StatutReservation.confirme])
            )
        )
    ).all()

    heures_reservees_7j = sum(
        (r.fin - r.debut).total_seconds() / 3600 for r in reservations_7j
    )
    heures_disponibles_7j = 7 * 24
    taux_occupation_7_jours = (heures_reservees_7j / heures_disponibles_7j * 100) if heures_disponibles_7j > 0 else 0

    return RessourceStatistics(
        total_reservations=total_reservations,
        reservations_actives=reservations_actives,
        reservations_a_venir=reservations_a_venir,
        taux_occupation_7_jours=round(taux_occupation_7_jours, 2),
        heures_reservees_30_jours=round(heures_reservees_30_jours, 2),
        reservation_moyenne_duree=round(reservation_moyenne_duree, 2)
    )


def get_prochaines_reservations(session, ressource_id: int, limit: int = 5) -> list[ReservationPublicSimple]:
    now = datetime.now()

    reservations = session.exec(
        select(Reservation)
        .where(
            and_(
                Reservation.ressource_id == ressource_id,
                Reservation.debut >= now,
                Reservation.statut.in_([StatutReservation.en_cours, StatutReservation.confirme])
            )
        )
        .order_by(Reservation.debut.asc())
        .limit(limit)
    ).all()

    return [
        ReservationPublicSimple(
            id=r.id,
            user_id=r.user_id,
            debut=r.debut,
            fin=r.fin,
            statut=r.statut,
            description=r.description,
            nbr_participants=r.nbr_participants
        )
        for r in reservations
    ]


def get_disponibilite_7_jours(session, ressource_id: int, ressource: Ressource) -> list[DisponibiliteJour]:
    now = datetime.now()
    disponibilites = []

    for i in range(7):
        jour = now + timedelta(days=i)
        date_str = jour.strftime("%Y-%m-%d")
        debut_jour = jour.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_jour = jour.replace(hour=23, minute=59, second=59, microsecond=999999)

        if ressource.etat != EtatRessource.active:
            disponibilites.append(DisponibiliteJour(
                date=date_str,
                est_disponible=False,
                raison_indisponibilite=f"Ressource {ressource.etat.value}",
                creneaux_disponibles=0
            ))
            continue

        indisponibilites = session.exec(
            select(ResourceAvailability)
            .where(
                and_(
                    ResourceAvailability.ressource_id == ressource_id,
                    ResourceAvailability.debut <= fin_jour,
                    ResourceAvailability.fin >= debut_jour,
                    ResourceAvailability.type_disponibilite != TypeDisponibilite.disponibilite_normale
                )
            )
        ).all()

        if indisponibilites:
            raison = ", ".join([i.raison_indisponibilite or i.type_disponibilite.value for i in indisponibilites])
            disponibilites.append(DisponibiliteJour(
                date=date_str,
                est_disponible=False,
                raison_indisponibilite=raison,
                creneaux_disponibles=0
            ))
            continue

        heures_ouverture = 10
        creneaux_total = heures_ouverture

        reservations = session.exec(
            select(Reservation)
            .where(
                and_(
                    Reservation.ressource_id == ressource_id,
                    Reservation.debut < fin_jour,
                    Reservation.fin > debut_jour,
                    Reservation.statut.in_([StatutReservation.en_cours, StatutReservation.confirme])
                )
            )
        ).all()

        heures_occupees = 0
        for r in reservations:
            debut_overlap = max(r.debut, debut_jour)
            fin_overlap = min(r.fin, fin_jour)
            heures_occupees += (fin_overlap - debut_overlap).total_seconds() / 3600

        creneaux_occupes = int(heures_occupees)
        creneaux_disponibles = max(0, creneaux_total - creneaux_occupes)

        disponibilites.append(DisponibiliteJour(
            date=date_str,
            est_disponible=creneaux_disponibles > 0,
            raison_indisponibilite=None,
            creneaux_disponibles=creneaux_disponibles
        ))

    return disponibilites