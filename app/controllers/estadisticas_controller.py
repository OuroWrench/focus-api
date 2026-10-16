"""Indicadores del usuario (los consumirá también el panel web de estadísticas)."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import usuario_actual
from app.models import Usuario
from app.schemas.estadisticas import EstadisticasRespuesta
from app.services.estadisticas_service import EstadisticasService

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])


@router.get("", response_model=EstadisticasRespuesta)
def estadisticas(desde: Optional[date] = None, hasta: Optional[date] = None,
                 u: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    return EstadisticasService(db).resumen(u.id, desde, hasta)
