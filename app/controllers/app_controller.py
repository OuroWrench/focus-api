"""CRUD de APP: aplicaciones del teléfono que el usuario quiere limitar."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import usuario_actual
from app.models import Usuario
from app.repositories.app_repository import AppRepository
from app.schemas.aplicacion import AppActualizar, AppCrear, AppRespuesta
from app.services.app_service import AppService

router = APIRouter(prefix="/apps", tags=["Apps"])


def get_service(db: Session = Depends(get_db)) -> AppService:
    return AppService(AppRepository(db))


@router.post("", response_model=AppRespuesta, status_code=status.HTTP_201_CREATED)
def crear_app(datos: AppCrear, u: Usuario = Depends(usuario_actual), service: AppService = Depends(get_service)):
    return service.crear(u.id, datos)


@router.get("", response_model=list[AppRespuesta])
def listar_apps(u: Usuario = Depends(usuario_actual), service: AppService = Depends(get_service)):
    return service.listar(u.id)


@router.get("/{numero}", response_model=AppRespuesta)
def obtener_app(numero: int, u: Usuario = Depends(usuario_actual), service: AppService = Depends(get_service)):
    return service.obtener(u.id, numero)


@router.put("/{numero}", response_model=AppRespuesta)
def actualizar_app(numero: int, cambios: AppActualizar, u: Usuario = Depends(usuario_actual),
                   service: AppService = Depends(get_service)):
    return service.actualizar(u.id, numero, cambios)


@router.delete("/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_app(numero: int, u: Usuario = Depends(usuario_actual), service: AppService = Depends(get_service)):
    service.eliminar(u.id, numero)
