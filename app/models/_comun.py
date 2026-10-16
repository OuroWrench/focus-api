"""Piezas compartidas por las tablas que pertenecen a un usuario."""
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import mapped_column


def ahora() -> datetime:
    """Fecha y hora actual en UTC (sin zona, para que SQLite y SQL Server la guarden igual)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DelUsuarioMixin:
    """Agrega usuario_id y numero a una tabla.

    - id: clave primaria global (uso interno y relaciones).
    - numero: consecutivo POR USUARIO (1, 2, 3...). Es el que aparece en las rutas:
      GET /pausas/7 con X-Usuario-Id: 1 -> la 7.ª pausa del usuario 1.
    """

    id = mapped_column(Integer, primary_key=True, autoincrement=True, sort_order=-10)
    numero = mapped_column(Integer, nullable=False, sort_order=-8)

    @classmethod
    def restriccion_numero(cls, tabla: str):
        return UniqueConstraint("usuario_id", "numero", name=f"uq_{tabla}_usuario_numero")


def fk_usuario():
    return mapped_column(Integer, ForeignKey("usuario.id"), nullable=False, index=True, sort_order=-9)
