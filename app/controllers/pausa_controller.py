"""CRUD de PAUSA: fricciones mostradas al abrir una app. /pausas/7 = 7.ª pausa del usuario del header."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import usuario_actual
from app.models import Usuario
from app.repositories.app_repository import AppRepository
from app.repositories.pausa_repository import PausaRepository
from app.schemas.pausa import PausaCrear, PausaActualizar, PausaRespuesta
from app.services.pausa_service import PausaService

router = APIRouter(prefix="/pausas", tags=["Pausas"])


def get_service(db: Session = Depends(get_db)) -> PausaService:
    return PausaService(PausaRepository(db), AppRepository(db))


@router.post("", response_model=PausaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_pausa(datos: PausaCrear, u: Usuario = Depends(usuario_actual), service: PausaService = Depends(get_service)):
    return service.crear(u.id, datos)


@router.get("", response_model=list[PausaRespuesta])
def listar_pausas(u: Usuario = Depends(usuario_actual), service: PausaService = Depends(get_service)):
    return service.listar(u.id)


@router.get("/{numero}", response_model=PausaRespuesta)
def obtener_pausa(numero: int, u: Usuario = Depends(usuario_actual), service: PausaService = Depends(get_service)):
    return service.obtener(u.id, numero)


@router.put("/{numero}", response_model=PausaRespuesta)
def actualizar_pausa(numero: int, cambios: PausaActualizar, u: Usuario = Depends(usuario_actual),
                     service: PausaService = Depends(get_service)):
    return service.actualizar(u.id, numero, cambios)


@router.delete("/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_pausa(numero: int, u: Usuario = Depends(usuario_actual), service: PausaService = Depends(get_service)):
    service.eliminar(u.id, numero)
