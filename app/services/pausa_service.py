from app.repositories.app_repository import AppRepository
from app.repositories.pausa_repository import PausaRepository
from app.services.base import ServicioPorUsuario
from app.utils.errores import NoEncontrado


class PausaService(ServicioPorUsuario):
    no_encontrado = "No existe la pausa {numero} para este usuario"

    def __init__(self, repo: PausaRepository, apps: AppRepository):
        super().__init__(repo)
        self.apps = apps

    def preparar_creacion(self, usuario_id: int, datos: dict) -> dict:
        app_numero = datos.pop("app_numero")
        app = self.apps.obtener(usuario_id, app_numero)
        if app is None:
            raise NoEncontrado(f"No existe la app {app_numero} para este usuario")
        datos["app_id"] = app.id
        return datos
