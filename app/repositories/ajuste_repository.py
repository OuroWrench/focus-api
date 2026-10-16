from sqlalchemy.orm import Session

from app.models import AjustePlan, Plan


class AjusteRepository:
    """Ajustes de un plan. Se identifican por (plan, semana)."""

    def __init__(self, db: Session):
        self.db = db

    def listar(self, plan: Plan) -> list[AjustePlan]:
        return self.db.query(AjustePlan).filter(AjustePlan.plan_id == plan.id).order_by(AjustePlan.semana).all()

    def obtener(self, plan: Plan, semana: int) -> AjustePlan | None:
        return self.db.query(AjustePlan).filter(AjustePlan.plan_id == plan.id, AjustePlan.semana == semana).first()

    def crear(self, plan: Plan, datos: dict) -> AjustePlan:
        ajuste = AjustePlan(plan_id=plan.id, **datos)
        self.db.add(ajuste)
        self.db.commit()
        self.db.refresh(ajuste)
        return ajuste

    def actualizar(self, ajuste: AjustePlan, cambios: dict) -> AjustePlan:
        for campo, valor in cambios.items():
            setattr(ajuste, campo, valor)
        self.db.commit()
        self.db.refresh(ajuste)
        return ajuste

    def eliminar(self, ajuste: AjustePlan) -> None:
        self.db.delete(ajuste)
        self.db.commit()
