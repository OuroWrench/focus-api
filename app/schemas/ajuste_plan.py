from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas._comun import Respuesta


class AjusteCrear(BaseModel):
    semana: int = Field(..., ge=1, examples=[2])
    uso_meta: float = Field(..., gt=0, description="Minutos meta de la semana", examples=[210])
    adherencia: float = Field(..., ge=0, le=1, description="Qué tanto se cumplió la meta (0 a 1)", examples=[0.85])
    cambio_pct: Optional[float] = Field(
        None, description="Si no se envía, se calcula con las reglas difusas de Focus!", examples=[None]
    )


class AjusteActualizar(BaseModel):
    uso_meta: Optional[float] = Field(None, gt=0)
    adherencia: Optional[float] = Field(None, ge=0, le=1)
    cambio_pct: Optional[float] = None


class AjusteRespuesta(Respuesta):
    semana: int
    uso_meta: float
    adherencia: float
    cambio_pct: float
    fecha: date
