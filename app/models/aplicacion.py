from sqlalchemy import Column, Integer, String

from app.database import Base
from app.models._comun import DelUsuarioMixin, fk_usuario


class App(DelUsuarioMixin, Base):
    """Aplicación del teléfono que el usuario quiere limitar."""

    __tablename__ = "app"
    __table_args__ = (DelUsuarioMixin.restriccion_numero("app"),)

    usuario_id = fk_usuario()
    nombre = Column(String(120), nullable=False)
    paquete = Column(String(255), nullable=False)
    categoria = Column(String(60), nullable=True)
    limite_aperturas = Column(Integer, nullable=False, default=10)
