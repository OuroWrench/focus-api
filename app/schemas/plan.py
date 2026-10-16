from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas._comun import Respuesta


class PlanCrear(BaseModel):
    fecha_inicio: date = Field(..., examples=["2026-10-19"])
    limite_base: int = Field(..., gt=0, description="Minutos diarios de pantalla", examples=[240])


class PlanActualizar(BaseModel):
    limite_base: Optional[int] = Field(None, gt=0)
    semana_actual: Optional[int] = Field(None, ge=1)
    activo: Optional[bool] = None


class PlanRespuesta(Respuesta):
    numero: int
    fecha_inicio: date
    limite_base: int
    semana_actual: int
    activo: bool
