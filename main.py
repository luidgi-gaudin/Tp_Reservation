from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, List

from fastapi import FastAPI, Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select

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


@app.get("/")
@app.post("/Site/")
def create_site(site: Site, session: SessionDep) -> Site | dict[str, str]:
    try:
        session.add(site)
        session.commit()
        session.refresh(site)
        return site
    except Exception as e:
        return {"error": str(e)}

@app.get("/Site/")
def get_sites(session: SessionDep) -> List[Site]:
    sites = session.exec(select(Site)).all()
    return sites


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


