from typing import Sequence, Any
from sqlmodel import select
from fastapi import HTTPException, APIRouter
from app.models.Site import Site
from app.database import SessionDep
from datetime import time as time_type
from main import internal_router

site_router = APIRouter(prefix="/sites", tags=["sites"])



@site_router.post("/")
def create_site(site: Site, session: SessionDep) -> Site | dict[str, str]:
    try:
        if isinstance(site.horaires_ouverture, str):
            h, m, s = map(int, site.horaires_ouverture.split(':'))
            site.horaires_ouverture = time_type(h, m, s)

        if isinstance(site.horaires_fermeture, str):
            h, m, s = map(int, site.horaires_fermeture.split(':'))
            site.horaires_fermeture = time_type(h, m, s)

        session.add(site)
        session.commit()
        session.refresh(site)
        return site
    except Exception as e:
        return {"error": str(e)}

@site_router.get("/")
def get_sites(session: SessionDep) -> Sequence[Any] | dict[str, str]:
    try:
        sites = session.exec(select(Site)).all()
        return sites
    except Exception as e:
        return {"error": str(e)}

@site_router.delete("/{site_id}")
def delete_site(site_id: int, session: SessionDep):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site Introuvable")
    session.delete(site)
    session.commit()
    return {"ok": True}