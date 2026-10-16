from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas._comun import Respuesta

TipoPausa = Literal["leve", "media", "alta"]


class PausaCrear(BaseModel):
    app_numero: int = Field(..., ge=1, examples=[1])
    tipo: TipoPausa = Field(..., examples=["media"])
    duracion_seg: int = Field(..., ge=0, examples=[15])
    ignorada: bool = False


class PausaActualizar(BaseModel):
    tipo: Optional[TipoPausa] = None
    duracion_seg: Optional[int] = Field(None, ge=0)
    ignorada: Optional[bool] = None


class PausaRespuesta(Respuesta):
    numero: int
    app_numero: int
    tipo: str
    duracion_seg: int
    ignorada: bool
    fecha: datetime
