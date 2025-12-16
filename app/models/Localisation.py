
from pydantic import BaseModel, Field


class Localisation(BaseModel):
    rue: str
    ville: str
    code_postal: int = Field(ge=10000, le=99999)
    pays: str = "France"