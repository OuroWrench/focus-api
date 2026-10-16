"""CRUD de DOMINIO_BLOQUEADO: sitios web que el usuario quiere bloquear."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import usuario_actual
from app.models import Usuario
from app.repositories.dominio_repository import DominioRepository
from app.schemas.dominio_bloqueado import DominioCrear, DominioActualizar, DominioRespuesta
from app.services.dominio_service import DominioService

router = APIRouter(prefix="/dominios", tags=["Dominios bloqueados"])


def get_service(db: Session = Depends(get_db)) -> DominioService:
    return DominioService(DominioRepository(db))


@router.post("", response_model=DominioRespuesta, status_code=status.HTTP_201_CREATED)
def crear_dominio(datos: DominioCrear, u: Usuario = Depends(usuario_actual), service: DominioService = Depends(get_service)):
    return service.crear(u.id, datos)


@router.get("", response_model=list[DominioRespuesta])
def listar_dominios(u: Usuario = Depends(usuario_actual), service: DominioService = Depends(get_service)):
    return service.listar(u.id)


@router.get("/{numero}", response_model=DominioRespuesta)
def obtener_dominio(numero: int, u: Usuario = Depends(usuario_actual), service: DominioService = Depends(get_service)):
    return service.obtener(u.id, numero)


@router.put("/{numero}", response_model=DominioRespuesta)
def actualizar_dominio(numero: int, cambios: DominioActualizar, u: Usuario = Depends(usuario_actual),
                     service: DominioService = Depends(get_service)):
    return service.actualizar(u.id, numero, cambios)


@router.delete("/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_dominio(numero: int, u: Usuario = Depends(usuario_actual), service: DominioService = Depends(get_service)):
    service.eliminar(u.id, numero)
