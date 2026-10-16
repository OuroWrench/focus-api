from sqlalchemy import Column, Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models._comun import ahora


class AjustePlan(Base):
    """Ajuste semanal de un plan. Se identifica por (plan, semana)."""

    __tablename__ = "ajuste_plan"
    __table_args__ = (UniqueConstraint("plan_id", "semana", name="uq_ajuste_plan_semana"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("plan.id"), nullable=False, index=True)
    semana = Column(Integer, nullable=False)
    uso_meta = Column(Float, nullable=False)       # minutos
    adherencia = Column(Float, nullable=False)     # 0.0 – 1.0
    cambio_pct = Column(Float, nullable=False)     # % de cambio al límite
    fecha = Column(Date, nullable=False, default=lambda: ahora().date())

    plan = relationship("Plan", back_populates="ajustes")
