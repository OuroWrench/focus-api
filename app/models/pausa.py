from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models._comun import DelUsuarioMixin, ahora, fk_usuario


class Pausa(DelUsuarioMixin, Base):
    """Pausa (fricción) mostrada al abrir una app."""

    __tablename__ = "pausa"
    __table_args__ = (DelUsuarioMixin.restriccion_numero("pausa"),)

    usuario_id = fk_usuario()
    app_id = Column(Integer, ForeignKey("app.id"), nullable=False, index=True)
    tipo = Column(String(30), nullable=False)          # leve | media | alta
    duracion_seg = Column(Integer, nullable=False)
    ignorada = Column(Boolean, nullable=False, default=False)
    fecha = Column(DateTime, nullable=False, default=ahora)

    app = relationship("App", lazy="joined")

    @property
    def app_numero(self) -> int:
        return self.app.numero
