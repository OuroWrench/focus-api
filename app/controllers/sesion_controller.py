"""CRUD de SESION_FOCO: sesiones de concentración (estilo Pomodoro)."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import usuario_actual
from app.models import Usuario
from app.repositories.sesion_repository import SesionRepository
from app.schemas.sesion_foco import SesionCrear, SesionActualizar, SesionRespuesta
from app.services.sesion_service import SesionService

router = APIRouter(prefix="/sesiones-foco", tags=["Sesiones de foco"])


def get_service(db: Session = Depends(get_db)) -> SesionService:
    return SesionService(SesionRepository(db))


@router.post("", response_model=SesionRespuesta, status_code=status.HTTP_201_CREATED)
def crear_sesion(datos: SesionCrear, u: Usuario = Depends(usuario_actual), service: SesionService = Depends(get_service)):
    return service.crear(u.id, datos)


@router.get("", response_model=list[SesionRespuesta])
def listar_sesiones(u: Usuario = Depends(usuario_actual), service: SesionService = Depends(get_service)):
    return service.listar(u.id)


@router.get("/{numero}", response_model=SesionRespuesta)
def obtener_sesion(numero: int, u: Usuario = Depends(usuario_actual), service: SesionService = Depends(get_service)):
    return service.obtener(u.id, numero)


@router.put("/{numero}", response_model=SesionRespuesta)
def actualizar_sesion(numero: int, cambios: SesionActualizar, u: Usuario = Depends(usuario_actual),
                     service: SesionService = Depends(get_service)):
    return service.actualizar(u.id, numero, cambios)


@router.delete("/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sesion(numero: int, u: Usuario = Depends(usuario_actual), service: SesionService = Depends(get_service)):
    service.eliminar(u.id, numero)
