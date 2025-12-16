from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from app.database import create_db_and_tables
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
app = FastAPI(lifespan=lifespan)
internal_router = APIRouter()
app.include_router(router=internal_router)



