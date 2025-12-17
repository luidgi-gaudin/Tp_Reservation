from typing import Annotated
from sqlmodel import select
from fastapi import HTTPException, APIRouter, Query
from app.models.Site import Site, SitePublic, SiteCreate, SiteUpdate
from app.database import SessionDep
from datetime import time as time_type

site_router = APIRouter(prefix="/sites", tags=["sites"])

def traduction_str_heure(heure: str) -> time_type:
    h, m, s = map(int, heure.split(':'))
    return time_type(h, m, s)


@site_router.post("/", response_model=SitePublic)
def create_site(site: SiteCreate, session: SessionDep):
    db_site = Site.model_validate(site)
    session.add(db_site)
    session.commit()
    session.refresh(db_site)
    return db_site


@site_router.get("/", response_model=list[SitePublic])
def get_sites(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    sites = session.exec(select(Site).offset(offset).limit(limit)).all()
    return sites


@site_router.get("/{site_id}", response_model=SitePublic)
def get_site(site_id: int, session: SessionDep):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site Introuvable")
    return site


@site_router.put("/{site_id}", response_model=SitePublic)
def update_site(site_id: int, site: SiteUpdate, session: SessionDep):
    site_db = session.get(Site, site_id)
    if not site_db:
        raise HTTPException(status_code=404, detail="Site Introuvable")
    site_data = site.model_dump(exclude_unset=True)
    site_db.sqlmodel_update(site_data)
    session.add(site_db)
    session.commit()
    session.refresh(site_db)
    return site_db


@site_router.delete("/{site_id}")
def delete_site(site_id: int, session: SessionDep):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site Introuvable")
    session.delete(site)
    session.commit()
    return {"ok": True}