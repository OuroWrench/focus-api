from app.models import DominioBloqueado
from app.repositories.base import RepositorioPorUsuario


class DominioRepository(RepositorioPorUsuario[DominioBloqueado]):
    modelo = DominioBloqueado

    def obtener_por_nombre(self, usuario_id: int, dominio: str) -> DominioBloqueado | None:
        return self._consulta(usuario_id).filter(DominioBloqueado.dominio == dominio).first()
