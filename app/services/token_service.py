from app.repositories.token_repository import TokenRepository
from app.services.base import ServicioPorUsuario
from app.utils.errores import Conflicto


class TokenService(ServicioPorUsuario):
    no_encontrado = "No existe el token {numero} para este usuario"
    repo: TokenRepository

    def preparar_creacion(self, usuario_id: int, datos: dict) -> dict:
        if self.repo.existe_token(datos["token"]):
            raise Conflicto("El token ya está registrado")
        return datos
