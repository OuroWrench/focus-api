from datetime import date, datetime, time, timedelta

from app.repositories.app_repository import AppRepository
from app.repositories.dominio_repository import DominioRepository
from app.repositories.evento_repository import EventoRepository
from app.repositories.pausa_repository import PausaRepository
from app.repositories.plan_repository import PlanRepository
from app.repositories.sesion_repository import SesionRepository


class EstadisticasService:
    def __init__(self, db):
        self.apps = AppRepository(db)
        self.eventos = EventoRepository(db)
        self.pausas = PausaRepository(db)
        self.sesiones = SesionRepository(db)
        self.dominios = DominioRepository(db)
        self.planes = PlanRepository(db)

    def resumen(self, usuario_id: int, desde: date | None, hasta: date | None) -> dict:
        inicio = datetime.combine(desde, time.min) if desde else None
        fin = datetime.combine(hasta + timedelta(days=1), time.min) if hasta else None
        total_eventos, segundos = self.eventos.resumen(usuario_id, inicio, fin)
        plan = self.planes.activo(usuario_id)
        return {
            "desde": desde,
            "hasta": hasta,
            "total_apps": self.apps.contar(usuario_id),
            "total_eventos": total_eventos,
            "minutos_uso": round(segundos / 60, 1),
            "total_pausas": self.pausas.contar(usuario_id),
            "pausas_ignoradas": self.pausas.contar(usuario_id, ignorada=True),
            "sesiones_foco": self.sesiones.contar(usuario_id),
            "sesiones_foco_completadas": self.sesiones.contar(usuario_id, completada=True),
            "minutos_foco_completados": self.sesiones.minutos_completados(usuario_id),
            "dominios_bloqueados_activos": self.dominios.contar(usuario_id, activo=True),
            "plan_activo": plan.numero if plan else None,
        }
