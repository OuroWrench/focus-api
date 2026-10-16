"""CRUD de TOKEN_DISPOSITIVO: tokens de notificaciones push de cada dispositivo."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import usuario_actual
from app.models import Usuario
from app.repositories.token_repository import TokenRepository
from app.schemas.token_dispositivo import TokenCrear, TokenActualizar, TokenRespuesta
from app.services.token_service import TokenService

router = APIRouter(prefix="/tokens-dispositivo", tags=["Tokens de dispositivo"])


def get_service(db: Session = Depends(get_db)) -> TokenService:
    return TokenService(TokenRepository(db))


@router.post("", response_model=TokenRespuesta, status_code=status.HTTP_201_CREATED)
def crear_token(datos: TokenCrear, u: Usuario = Depends(usuario_actual), service: TokenService = Depends(get_service)):
    return service.crear(u.id, datos)


@router.get("", response_model=list[TokenRespuesta])
def listar_tokens(u: Usuario = Depends(usuario_actual), service: TokenService = Depends(get_service)):
    return service.listar(u.id)


@router.get("/{numero}", response_model=TokenRespuesta)
def obtener_token(numero: int, u: Usuario = Depends(usuario_actual), service: TokenService = Depends(get_service)):
    return service.obtener(u.id, numero)


@router.put("/{numero}", response_model=TokenRespuesta)
def actualizar_token(numero: int, cambios: TokenActualizar, u: Usuario = Depends(usuario_actual),
                     service: TokenService = Depends(get_service)):
    return service.actualizar(u.id, numero, cambios)


@router.delete("/{numero}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_token(numero: int, u: Usuario = Depends(usuario_actual), service: TokenService = Depends(get_service)):
    service.eliminar(u.id, numero)
