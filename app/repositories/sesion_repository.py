from sqlalchemy import func, true

from app.models import SesionFoco
from app.repositories.base import RepositorioPorUsuario


class SesionRepository(RepositorioPorUsuario[SesionFoco]):
    modelo = SesionFoco

    def minutos_completados(self, usuario_id: int) -> int:
        total = self.db.query(func.coalesce(func.sum(SesionFoco.duracion_min), 0)) \
            .filter(SesionFoco.usuario_id == usuario_id, SesionFoco.completada == true()).scalar()
        return int(total)
