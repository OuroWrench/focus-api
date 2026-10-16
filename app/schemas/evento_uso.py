from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas._comun import Respuesta


class EventoCrear(BaseModel):
    app_numero: int = Field(..., ge=1, description="Número de la app del usuario", examples=[1])
    franja_id: Optional[int] = Field(None, examples=[1])
    inicio: datetime = Field(..., examples=["2026-10-19T08:15:00"])
    fin: datetime = Field(..., examples=["2026-10-19T08:30:00"])

    @model_validator(mode="after")
    def validar_rango(self):
        if self.fin <= self.inicio:
            raise ValueError("fin debe ser posterior a inicio")
        return self


class EventoActualizar(BaseModel):
    franja_id: Optional[int] = None
    inicio: Optional[datetime] = None
    fin: Optional[datetime] = None


class EventoRespuesta(Respuesta):
    numero: int
    app_numero: int
    franja_id: Optional[int] = None
    inicio: datetime
    fin: datetime
    duracion_seg: int
