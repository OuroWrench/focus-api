from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas._comun import Respuesta


class SesionCrear(BaseModel):
    duracion_min: int = Field(..., gt=0, le=600, examples=[25])


class SesionActualizar(BaseModel):
    completada: Optional[bool] = Field(None, description="Al marcarla, se registra la hora de fin")
    fin: Optional[datetime] = None
    duracion_min: Optional[int] = Field(None, gt=0, le=600)


class SesionRespuesta(Respuesta):
    numero: int
    inicio: datetime
    fin: Optional[datetime] = None
    duracion_min: int
    completada: bool
