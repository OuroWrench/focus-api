from sqlalchemy import Boolean, Column, String

from app.database import Base
from app.models._comun import DelUsuarioMixin, fk_usuario


class DominioBloqueado(DelUsuarioMixin, Base):
    __tablename__ = "dominio_bloqueado"
    __table_args__ = (DelUsuarioMixin.restriccion_numero("dominio_bloqueado"),)

    usuario_id = fk_usuario()
    dominio = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
