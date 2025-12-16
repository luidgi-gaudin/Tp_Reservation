from contextlib import asynccontextmanager
from pathlib import Path
from sys import intern
from typing import Annotated, Any, Sequence

from fastapi import FastAPI, APIRouter

from app.database import create_db_and_tables, SessionDep
from app.models.Site import Site
from app.models.User import User
from app.models.Department import Department
from app.models.Ressource import Ressource
from app.models.Reservation import Reservation
from app.router.sites import site_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
app = FastAPI(lifespan=lifespan)

app.include_router(router=site_router)



