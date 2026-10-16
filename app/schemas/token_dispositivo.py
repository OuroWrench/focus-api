from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas._comun import Respuesta


class TokenCrear(BaseModel):
    token: str = Field(..., min_length=10, max_length=512, examples=["fcm-ejemplo-0123456789abcdef"])
    plataforma: Literal["android", "web"] = "android"


class TokenActualizar(BaseModel):
    activo: Optional[bool] = None


class TokenRespuesta(Respuesta):
    numero: int
    token: str
    plataforma: str
    fecha_registro: datetime
    activo: bool
