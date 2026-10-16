from datetime import datetime

from app.repositories.app_repository import AppRepository
from app.repositories.evento_repository import EventoRepository
from app.repositories.franja_repository import FranjaRepository
from app.services.base import ServicioPorUsuario
from app.utils.errores import Conflicto, NoEncontrado


class EventoService(ServicioPorUsuario):
    no_encontrado = "No existe el evento {numero} para este usuario"
    campos_anulables = {"franja_id"}
    repo: EventoRepository

    def __init__(self, repo: EventoRepository, apps: AppRepository, franjas: FranjaRepository):
        super().__init__(repo)
        self.apps = apps
        self.franjas = franjas

    def _app_id(self, usuario_id: int, app_numero: int) -> int:
        app = self.apps.obtener(usuario_id, app_numero)
        if app is None:
            raise NoEncontrado(f"No existe la app {app_numero} para este usuario")
        return app.id

    def _validar_franja(self, franja_id: int | None) -> None:
        if franja_id is not None and self.franjas.obtener(franja_id) is None:
            raise NoEncontrado(f"No existe la franja {franja_id}")

    def listar_filtrado(self, usuario_id: int, app_numero: int | None, franja_id: int | None,
                        desde: datetime | None, hasta: datetime | None):
        app_id = self._app_id(usuario_id, app_numero) if app_numero is not None else None
        return self.repo.listar_filtrado(usuario_id, app_id, franja_id, desde, hasta)

    def preparar_creacion(self, usuario_id: int, datos: dict) -> dict:
        datos["app_id"] = self._app_id(usuario_id, datos.pop("app_numero"))
        self._validar_franja(datos.get("franja_id"))
        datos["duracion_seg"] = int((datos["fin"] - datos["inicio"]).total_seconds())
        return datos

    def preparar_actualizacion(self, usuario_id: int, evento, cambios: dict) -> dict:
        if "franja_id" in cambios:
            self._validar_franja(cambios["franja_id"])
        inicio = cambios.get("inicio", evento.inicio)
        fin = cambios.get("fin", evento.fin)
        if fin <= inicio:
            raise Conflicto("fin debe ser posterior a inicio")
        cambios["duracion_seg"] = int((fin - inicio).total_seconds())
        return cambios
