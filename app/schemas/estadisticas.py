from datetime import date
from typing import Optional

from pydantic import BaseModel


class EstadisticasRespuesta(BaseModel):
    desde: Optional[date] = None
    hasta: Optional[date] = None
    total_apps: int
    total_eventos: int
    minutos_uso: float
    total_pausas: int
    pausas_ignoradas: int
    sesiones_foco: int
    sesiones_foco_completadas: int
    minutos_foco_completados: int
    dominios_bloqueados_activos: int
    plan_activo: Optional[int] = None
