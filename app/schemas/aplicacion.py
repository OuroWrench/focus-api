from typing import Optional

from pydantic import BaseModel, Field

from app.schemas._comun import Respuesta


class AppCrear(BaseModel):
    nombre: str = Field(..., max_length=120, examples=["Instagram"])
    paquete: str = Field(..., max_length=255, examples=["com.instagram.android"])
    categoria: Optional[str] = Field(None, max_length=60, examples=["redes"])
    limite_aperturas: int = Field(10, ge=0, examples=[5])


class AppActualizar(BaseModel):
    nombre: Optional[str] = Field(None, max_length=120)
    paquete: Optional[str] = Field(None, max_length=255)
    categoria: Optional[str] = Field(None, max_length=60)
    limite_aperturas: Optional[int] = Field(None, ge=0)


class AppRespuesta(Respuesta):
    numero: int
    nombre: str
    paquete: str
    categoria: Optional[str] = None
    limite_aperturas: int
