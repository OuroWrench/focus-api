from app.models import TokenDispositivo
from app.repositories.base import RepositorioPorUsuario


class TokenRepository(RepositorioPorUsuario[TokenDispositivo]):
    modelo = TokenDispositivo

    def existe_token(self, token: str) -> bool:
        return self.db.query(TokenDispositivo.id).filter(TokenDispositivo.token == token).first() is not None
