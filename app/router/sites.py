from typing import Sequence, Any
from sqlmodel import select
from fastapi import HTTPException, APIRouter
from app.models.Site import Site
from app.database import SessionDep
from datetime import time as time_type

site_router = APIRouter(prefix="/sites", tags=["sites"])

def traduction_str_heure(heure: str) -> time_type:
    h, m, s = map(int, heure.split(':'))
    return time_type(h, m, s)


@site_router.post("/")
def create_site(site: Site, session: SessionDep) -> Site | dict[str, str]:
    try:
        if isinstance(site.horaires_ouverture, str):
            site.horaires_ouverture = traduction_str_heure(site.horaires_ouverture)

        if isinstance(site.horaires_fermeture, str):
            site.horaires_fermeture = traduction_str_heure(site.horaires_fermeture)

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

@site_router.get("/{site_id}")
def get_site(site_id: int, session: SessionDep):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site Introuvable")
    return site

@site_router.put("/{site_id}")
def update_site(site_id: int, site: Site, session: SessionDep):

    if isinstance(site.horaires_ouverture, str):
        site.horaires_ouverture = traduction_str_heure(site.horaires_ouverture)

    if isinstance(site.horaires_fermeture, str):
        site.horaires_fermeture = traduction_str_heure(site.horaires_fermeture)

    site_db = session.get(Site, site_id)
    if not site_db:
        raise HTTPException(status_code=404, detail="Site Introuvable")
    site_data = site.model_dump(exclude_unset=True)
    site_db.sqlmodel_update(site_data)
    session.add(site_db)
    session.commit()
    session.refresh(site_db)
    return site_db