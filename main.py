from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from app.database import create_db_and_tables
from app.models.Site import Site
from app.models.User import User
from app.models.Department import Department
from app.models.Ressource import Ressource
from app.models.Reservation import Reservation
from app.models.ResourceAvailability import ResourceAvailability
from app.router.ressources import ressources_router
from app.router.sites import site_router
from app.router.auth import auth_router
from app.middleware import AuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(AuthMiddleware)


internal_router = APIRouter()
internal_router.include_router(auth_router)
internal_router.include_router(site_router)
internal_router.include_router(ressources_router)

app.include_router(router=internal_router)



