from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

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