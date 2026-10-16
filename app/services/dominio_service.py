from app.repositories.dominio_repository import DominioRepository
from app.services.base import ServicioPorUsuario
from app.utils.errores import Conflicto


class DominioService(ServicioPorUsuario):
    no_encontrado = "No existe el dominio {numero} para este usuario"
    repo: DominioRepository

    def preparar_creacion(self, usuario_id: int, datos: dict) -> dict:
        datos["dominio"] = datos["dominio"].lower()
        if self.repo.obtener_por_nombre(usuario_id, datos["dominio"]):
            raise Conflicto("Ese dominio ya está en la lista")
        return datos

    def preparar_actualizacion(self, usuario_id: int, obj, cambios: dict) -> dict:
        if "dominio" in cambios:
            cambios["dominio"] = cambios["dominio"].lower()
            otro = self.repo.obtener_por_nombre(usuario_id, cambios["dominio"])
            if otro and otro.id != obj.id:
                raise Conflicto("Ese dominio ya está en la lista")
        return cambios
