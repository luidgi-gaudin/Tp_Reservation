from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter

from app.database.database import create_db_and_tables
from app.router.ressources import ressources_router
from app.router.sites import site_router
from app.router.auth import auth_router
from app.router.departments import department_router
from app.middleware.middleware import AuthMiddleware


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
internal_router.include_router(department_router)
app.include_router(router=internal_router)