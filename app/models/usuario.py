from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base
from app.models._comun import ahora


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, default=ahora, nullable=False)
    seudonimo = Column(String(60), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    foto_url = Column(String(1000), nullable=True)
