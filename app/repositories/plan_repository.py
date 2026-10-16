from sqlalchemy import true

from app.models import Plan
from app.repositories.base import RepositorioPorUsuario


class PlanRepository(RepositorioPorUsuario[Plan]):
    modelo = Plan

    def activo(self, usuario_id: int) -> Plan | None:
        return self._consulta(usuario_id).filter(Plan.activo == true()).order_by(Plan.numero.desc()).first()

    def desactivar_todos(self, usuario_id: int) -> None:
        self._consulta(usuario_id).filter(Plan.activo == true()).update({Plan.activo: False})
        self.db.commit()
