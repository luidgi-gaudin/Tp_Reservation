from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, EmailStr

from app.models.Department import Department
from app.models.Enum.TypePriorite import TypePriorite
from app.models.Enum.TypeRole import TypeRole


class User(BaseModel):
    id: int = Field(gt=0)
    nomUtilisateur: str = Field(min_length=3)
    email: EmailStr
    nomPrenom: str = Field(min_length=3)
    role: TypeRole
    departement: Department
    autorisation: List[str] = Field(default_factory=list)
    priorite: TypePriorite
    compteActif: bool
    dateCreation: datetime = Field(default_factory=datetime.now)