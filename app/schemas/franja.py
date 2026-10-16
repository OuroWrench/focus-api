from datetime import date, time
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas._comun import Respuesta


class FranjaCrear(BaseModel):
    fecha: date = Field(..., examples=["2026-10-19"])
    hora_inicio: time = Field(..., examples=["08:00"])
    hora_fin: time = Field(..., examples=["10:00"])

    @model_validator(mode="after")
    def validar_horas(self):
        if self.hora_fin <= self.hora_inicio and self.hora_fin != time(0, 0):
            raise ValueError("hora_fin debe ser posterior a hora_inicio")
        return self


class FranjaActualizar(BaseModel):
    fecha: Optional[date] = None
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None


class FranjasGenerar(BaseModel):
    fecha: date = Field(..., examples=["2026-10-19"])


class FranjaRespuesta(Respuesta):
    id: int
    fecha: date
    hora_inicio: time
    hora_fin: time
