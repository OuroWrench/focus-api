from typing import Optional

from pydantic import BaseModel, Field

from app.schemas._comun import Respuesta

PATRON_DOMINIO = r"^[A-Za-z0-9][A-Za-z0-9-]*(\.[A-Za-z0-9-]+)+$"


class DominioCrear(BaseModel):
    dominio: str = Field(..., max_length=255, pattern=PATRON_DOMINIO, examples=["youtube.com"])


class DominioActualizar(BaseModel):
    dominio: Optional[str] = Field(None, max_length=255, pattern=PATRON_DOMINIO)
    activo: Optional[bool] = None


class DominioRespuesta(Respuesta):
    numero: int
    dominio: str
    activo: bool
