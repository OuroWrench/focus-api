from sqlalchemy import Boolean, Column, DateTime, Integer

from app.database import Base
from app.models._comun import DelUsuarioMixin, ahora, fk_usuario


class SesionFoco(DelUsuarioMixin, Base):
    __tablename__ = "sesion_foco"
    __table_args__ = (DelUsuarioMixin.restriccion_numero("sesion_foco"),)

    usuario_id = fk_usuario()
    inicio = Column(DateTime, nullable=False, default=ahora)
    fin = Column(DateTime, nullable=True)
    duracion_min = Column(Integer, nullable=False)     # duración planeada
    completada = Column(Boolean, nullable=False, default=False)
