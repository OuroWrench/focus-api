from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base
from app.models._comun import DelUsuarioMixin, fk_usuario


class EventoUso(DelUsuarioMixin, Base):
    """Uso agregado de una app (sin contenido, solo tiempos)."""

    __tablename__ = "evento_uso"
    __table_args__ = (DelUsuarioMixin.restriccion_numero("evento_uso"),)

    usuario_id = fk_usuario()
    app_id = Column(Integer, ForeignKey("app.id"), nullable=False, index=True)
    franja_id = Column(Integer, ForeignKey("franja.id"), nullable=True, index=True)
    inicio = Column(DateTime, nullable=False)
    fin = Column(DateTime, nullable=False)
    duracion_seg = Column(Integer, nullable=False)

    app = relationship("App", lazy="joined")

    @property
    def app_numero(self) -> int:
        return self.app.numero
