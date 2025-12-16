from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any, Sequence

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select
from datetime import time as time_type

from app.models.Site import Site
from app.models.User import User
from app.models.Department import Department
from app.models.Ressource import Ressource
from app.models.Reservation import Reservation

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield


sqlite_file_name = "resa.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
        db_path_abs = Path(engine.url.database).resolve()
        print("DB file (relative):", engine.url.database)
        print("DB file (absolute):", db_path_abs)
        SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
app = FastAPI(lifespan=lifespan)


@app.post("/site/")
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

@app.get("/site/")
def get_sites(session: SessionDep) -> Sequence[Any] | dict[str, str]:
    try:
        sites = session.exec(select(Site)).all()
        return sites
    except Exception as e:
        return {"error": str(e)}

@app.delete("/site/{site_id}")
def delete_site(site_id: int, session: SessionDep):
    site = session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site Introuvable")
    session.delete(site)
    session.commit()
    return {"ok": True}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


