"""CRUD de FRANJA: catálogo global de franjas de 2 horas (no depende del usuario)."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.franja_repository import FranjaRepository
from app.schemas.franja import FranjaActualizar, FranjaCrear, FranjaRespuesta, FranjasGenerar
from app.services.franja_service import FranjaService

router = APIRouter(prefix="/franjas", tags=["Franjas"])


def get_service(db: Session = Depends(get_db)) -> FranjaService:
    return FranjaService(FranjaRepository(db))


@router.post("", response_model=FranjaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_franja(datos: FranjaCrear, service: FranjaService = Depends(get_service)):
    return service.crear(datos)


@router.post("/generar", response_model=list[FranjaRespuesta], status_code=status.HTTP_201_CREATED)
def generar_franjas(datos: FranjasGenerar, service: FranjaService = Depends(get_service)):
    """Crea las 12 franjas de 2 horas de una fecha (solo las que falten)."""
    return service.generar_dia(datos.fecha)


@router.get("", response_model=list[FranjaRespuesta])
def listar_franjas(fecha: Optional[date] = None, service: FranjaService = Depends(get_service)):
    return service.listar(fecha)


@router.get("/{franja_id}", response_model=FranjaRespuesta)
def obtener_franja(franja_id: int, service: FranjaService = Depends(get_service)):
    return service.obtener(franja_id)


@router.put("/{franja_id}", response_model=FranjaRespuesta)
def actualizar_franja(franja_id: int, cambios: FranjaActualizar, service: FranjaService = Depends(get_service)):
    return service.actualizar(franja_id, cambios)


@router.delete("/{franja_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_franja(franja_id: int, service: FranjaService = Depends(get_service)):
    service.eliminar(franja_id)
