from typing import Annotated, Optional, Literal

from fastapi import APIRouter, HTTPException
from fastapi.params import Query
from sqlmodel import select

from app.database import SessionDep
from app.models.Enum.TypeRessource import TypeRessource
from app.models.Ressource import (
    Ressource,
    RessourcePublic,
    RessourceCreate,
    RessourceUpdate,
    RessourceListResponse,
    RessourceDetailResponse,
)
from app.services.ressources import (
    ressource_list,
    get_ressource_statistics,
    get_prochaines_reservations,
    get_disponibilite_7_jours,
)

ressources_router = APIRouter(prefix="/ressources", tags=["ressources"])


@ressources_router.get("/", response_model=RessourceListResponse)
async def get_ressources(
        session: SessionDep,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=200)] = 100,

        type_of_ressource: Optional[TypeRessource] = None,
        site_id: Optional[int] = None,

        batiment: Optional[str] = None,

        disponible: Optional[bool] = None,
        caracteristiques: Optional[str] = None,
        minimum_capacity: Annotated[int, Query(ge=0)] = 0,

        sort_by: Annotated[Literal["nom", "capacite", "type"], Query()] = "nom",
        sort_order: Annotated[Literal["asc", "desc"], Query()] = "asc",
):
    return ressource_list(
        session,
        offset=offset,
        limit=limit,
        type_of_ressource=type_of_ressource,
        site_id=site_id,
        batiment=batiment,
        disponible=disponible,
        caracteristiques=caracteristiques,
        minimum_capacity=minimum_capacity,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@ressources_router.get("/{ressource_id}", response_model=RessourceDetailResponse)
async def get_ressource(ressource_id: int, session: SessionDep):
    ressource = session.get(Ressource, ressource_id)
    if not ressource:
        raise HTTPException(status_code=404, detail="Ressource Introuvable")

    statistiques = get_ressource_statistics(session, ressource_id)
    prochaines_reservations = get_prochaines_reservations(session, ressource_id, limit=5)
    disponibilite_7_jours = get_disponibilite_7_jours(session, ressource_id, ressource)

    return RessourceDetailResponse(
        ressource=RessourcePublic.model_validate(ressource),
        statistiques=statistiques,
        prochaines_reservations=prochaines_reservations,
        disponibilite_7_jours=disponibilite_7_jours
    )


@ressources_router.post("/", response_model=RessourcePublic)
async def create_ressource(ressource: RessourceCreate, session: SessionDep):
    if session.exec(select(Ressource).where(Ressource.nom == ressource.nom)).one() is not None:
        raise HTTPException(status_code=403, detail="ce nom de ressource est déja utiliser !")
    db_ressource = Ressource.model_validate(ressource)
    session.add(db_ressource)
    session.commit()
    session.refresh(db_ressource)
    return db_ressource


@ressources_router.put("/{ressource_id}", response_model=RessourcePublic)
async def update_ressource(ressource_id: int, ressource: RessourceUpdate, session: SessionDep):
    ressource_db = session.get(Ressource, ressource_id)
    if not ressource_db:
        raise HTTPException(status_code=404, detail="Ressource Introuvable")
    ressource_data = ressource.model_dump(exclude_unset=True)
    ressource_db.sqlmodel_update(ressource_data)
    session.add(ressource_db)
    session.commit()
    session.refresh(ressource_db)
    return ressource_db


@ressources_router.delete("/{ressource_id}")
async def delete_ressource(ressource_id: int, session: SessionDep):
    ressource = session.get(Ressource, ressource_id)
    if not ressource:
        raise HTTPException(status_code=404, detail="Ressource Introuvable")
    session.delete(ressource)
    session.commit()
    return {"ok": True}