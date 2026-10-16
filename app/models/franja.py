from sqlalchemy import Column, Date, Integer, Time, UniqueConstraint

from app.database import Base


class Franja(Base):
    """Franja horaria de 2 horas. Es un catálogo global (no pertenece a un usuario)."""

    __tablename__ = "franja"
    __table_args__ = (UniqueConstraint("fecha", "hora_inicio", name="uq_franja_fecha_hora"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False, index=True)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
