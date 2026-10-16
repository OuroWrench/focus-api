from app.repositories.ajuste_repository import AjusteRepository
from app.repositories.plan_repository import PlanRepository
from app.services.base import ServicioPorUsuario
from app.utils.errores import Conflicto, NoEncontrado
from app.utils.reglas_plan import calcular_cambio


class PlanService(ServicioPorUsuario):
    no_encontrado = "No existe el plan {numero} para este usuario"
    repo: PlanRepository

    def crear(self, usuario_id: int, datos):
        # Solo puede haber un plan activo: el nuevo reemplaza al anterior.
        self.repo.desactivar_todos(usuario_id)
        return super().crear(usuario_id, datos)

    def activo(self, usuario_id: int):
        plan = self.repo.activo(usuario_id)
        if plan is None:
            raise NoEncontrado("El usuario no tiene un plan activo")
        return plan


class AjusteService:
    def __init__(self, planes: PlanService, repo: AjusteRepository):
        self.planes = planes
        self.repo = repo

    def listar(self, usuario_id: int, plan_numero: int):
        return self.repo.listar(self.planes.obtener(usuario_id, plan_numero))

    def obtener(self, usuario_id: int, plan_numero: int, semana: int):
        plan = self.planes.obtener(usuario_id, plan_numero)
        ajuste = self.repo.obtener(plan, semana)
        if ajuste is None:
            raise NoEncontrado(f"El plan {plan_numero} no tiene ajuste en la semana {semana}")
        return ajuste

    def crear(self, usuario_id: int, plan_numero: int, datos):
        plan = self.planes.obtener(usuario_id, plan_numero)
        if self.repo.obtener(plan, datos.semana):
            raise Conflicto(f"Ya existe un ajuste para la semana {datos.semana}")
        valores = datos.model_dump()
        if valores["cambio_pct"] is None:
            valores["cambio_pct"], _ = calcular_cambio(valores["adherencia"])
        ajuste = self.repo.crear(plan, valores)
        if datos.semana > plan.semana_actual:
            self.planes.repo.actualizar(plan, {"semana_actual": datos.semana})
        return ajuste

    def actualizar(self, usuario_id: int, plan_numero: int, semana: int, cambios):
        ajuste = self.obtener(usuario_id, plan_numero, semana)
        datos = {k: v for k, v in cambios.model_dump(exclude_unset=True).items() if v is not None}
        if "adherencia" in datos and "cambio_pct" not in datos:
            datos["cambio_pct"], _ = calcular_cambio(datos["adherencia"])
        return self.repo.actualizar(ajuste, datos) if datos else ajuste

    def eliminar(self, usuario_id: int, plan_numero: int, semana: int) -> None:
        self.repo.eliminar(self.obtener(usuario_id, plan_numero, semana))
