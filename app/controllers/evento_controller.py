"""CRUD de EVENTO_USO: registros agregados de uso de cada app."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import usuario_actual
from app.models import Usuario
from app.repositories.app_repository import AppRepository
from app.repositories.evento_repository import EventoRepository
from app.repositories.franja_repository import FranjaRepository
from app.schemas.evento_uso import EventoActualizar, EventoCrear, EventoRespuesta
from app.services.evento_service import EventoService

router = APIRouter(prefix="/eventos", tags=["Eventos de uso"])


def get_service(db: Session = Depends(get_db)) -> EventoService:
    return EventoService(EventoRepository(db), AppRepository(db), FranjaRepository(db))


@router.post("", response_model=EventoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_evento(datos: EventoCrear, u: Usuario = Depends(usuario_actual),
                 service: EventoService = Depends(get_service)):
    return service.crear(u.id, datos)


@router.get("", response_model=list[EventoRespuesta])
def listar_eventos(app_numero: Optional[int] = None, franja_id: Optional[int] = None,
                   desde: Optional[datetime] = None, hasta: Optional[datetime] = None,
                   u: Usuario = Depends(usuario_actual), service: EventoService = Depends(get_service)):
    return service.listar_filtrado(u.id, app_numero, franja_id, desde, hasta)


@router.get("/{numero}", response_model=EventoRespuesta)
def obtener_evento(numero: int, u: Usuario = Depends(usuario_actual), service: EventoService = Depends(get_service)):
    return service.obtener(u.id, numero)


@router.put("/{numero}", response_model=EventoRespuesta)
def actualizar_evento(numero: int, cambios: EventoActualizar, u: Usuario = Depends(usuario_actual),
                      service: EventoService = Depends(get_service)):
    return service.actualizar(u.id, numero, cambios)


@router.delete("/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_evento(numero: int, u: Usuario = Depends(usuario_actual), service: EventoService = Depends(get_service)):
    service.eliminar(u.id, numero)
