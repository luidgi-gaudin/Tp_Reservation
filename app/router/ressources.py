from typing import Annotated, Optional, Literal

from fastapi import APIRouter
from fastapi.params import Query

from app.database import SessionDep
from app.models.Enum.TypeRessource import TypeRessource
from app.models.Ressource import Ressource
from app.services.ressources import ressource_list

ressources_router = APIRouter(prefix="/ressources", tags=["ressources"])


@ressources_router.get("/")
async def get_ressources(
        session: SessionDep,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=200)] = 100,

        type_of_ressource: Optional[TypeRessource] = None,
        site_id: Optional[int] = None,

        ville: Optional[str] = None,
        code_postal: Optional[int] = None,

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
        ville=ville,
        code_postal=code_postal,
        disponible=disponible,
        caracteristiques=caracteristiques,
        minimum_capacity=minimum_capacity,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@ressources_router.get("/{ressource_id}")
async def get_ressource(ressource_id: int, session: SessionDep):
    ressource = session.get(Ressource, ressource_id)
    return ressource


@ressources_router.post("/")
async def create_ressource(ressource: Ressource, session: SessionDep):
    session.add(ressource)
    session.commit()
    session.refresh(ressource)
    return ressource