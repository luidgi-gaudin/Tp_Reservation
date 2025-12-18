from typing import Annotated
from sqlmodel import select
from fastapi import HTTPException, APIRouter, Query, Request
from app.models.Department import Department, DepartmentPublic, DepartmentCreate, DepartmentUpdate
from app.models.User import User
from app.models.Enum.TypeRole import TypeRole
from app.database.database import SessionDep
from app.helpers.auth.permissions import require_manager_or_admin, require_admin

department_router = APIRouter(prefix="/departments", tags=["departments"])


@department_router.post("/", response_model=DepartmentPublic)
def create_department(department: DepartmentCreate, request: Request, session: SessionDep):
    require_manager_or_admin(request)
    manager = session.get(User, department.manager_id)
    if not manager:
        raise HTTPException(status_code=404, detail="Manager Introuvable")
    if manager.role not in [TypeRole.manager, TypeRole.admin]:
        raise HTTPException(status_code=403, detail="L'utilisateur sélectionné doit être manager ou admin")
    db_department = Department.model_validate(department)
    session.add(db_department)
    session.commit()
    session.refresh(db_department)
    return db_department


@department_router.get("/", response_model=list[DepartmentPublic])
def get_departments(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
):
    departments = session.exec(select(Department).offset(offset).limit(limit)).all()
    return departments


@department_router.get("/{department_id}", response_model=DepartmentPublic)
def get_department(department_id: int, session: SessionDep):
    department = session.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department Introuvable")
    return department


@department_router.put("/{department_id}", response_model=DepartmentPublic)
def update_department(department_id: int, department: DepartmentUpdate, request: Request, session: SessionDep):
    require_manager_or_admin(request)
    department_db = session.get(Department, department_id)
    if not department_db:
        raise HTTPException(status_code=404, detail="Department Introuvable")
    if department.manager_id is not None:
        manager = session.get(User, department.manager_id)
        if not manager:
            raise HTTPException(status_code=404, detail="Manager Introuvable")
        if manager.role not in [TypeRole.manager, TypeRole.admin]:
            raise HTTPException(status_code=403, detail="L'utilisateur sélectionné doit être manager ou admin")
    department_data = department.model_dump(exclude_unset=True)
    department_db.sqlmodel_update(department_data)
    session.add(department_db)
    session.commit()
    session.refresh(department_db)
    return department_db


@department_router.delete("/{department_id}")
def delete_department(department_id: int, request: Request, session: SessionDep):
    require_admin(request)
    department = session.get(Department, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department Introuvable")
    session.delete(department)
    session.commit()
    return {"ok": True}