from typing import Optional, Literal

from sqlmodel import select
from sqlalchemy import func

from app.models.Ressource import Ressource
from app.models.Enum.TypeRessource import TypeRessource
from app.models.Enum.EtatRessource import EtatRessource


def ressource_list(
    session,
    *,
    offset: int = 0,
    limit: int = 100,
    type_of_ressource: Optional[TypeRessource] = None,
    site_id: Optional[int] = None,
    ville: Optional[str] = None,
    code_postal: Optional[int] = None,
    disponible: Optional[bool] = None,
    caracteristiques: Optional[str] = None,  # ex: "projector,whiteboard"
    minimum_capacity: int = 0,
    sort_by: Literal["nom", "capacite", "type"] = "nom",
    sort_order: Literal["asc", "desc"] = "asc",
) -> dict:
    conditions = []

    if type_of_ressource is not None:
        conditions.append(Ressource.type_ressource == type_of_ressource)

    if site_id is not None:
        conditions.append(Ressource.site_id == site_id)

    if ville:
        conditions.append(Ressource.localisation_ville.ilike(f"%{ville}%"))

    if code_postal is not None:
        conditions.append(Ressource.localisation_code_postal == code_postal)

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