"""
Repositorio genérico para las tablas que pertenecen a un usuario.

Es la ÚNICA capa que sabe que existe SQLAlchemy. Todas las consultas
filtran por usuario_id, así un usuario nunca ve registros de otro.
"""
from typing import Generic, TypeVar

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

M = TypeVar("M")


class RepositorioPorUsuario(Generic[M]):
    modelo: type[M]

    def __init__(self, db: Session):
        self.db = db

    def _consulta(self, usuario_id: int):
        return self.db.query(self.modelo).filter(self.modelo.usuario_id == usuario_id)

    def listar(self, usuario_id: int, **filtros) -> list[M]:
        consulta = self._consulta(usuario_id)
        for campo, valor in filtros.items():
            if valor is not None:
                consulta = consulta.filter(getattr(self.modelo, campo) == valor)
        return consulta.order_by(self.modelo.numero).all()

    def obtener(self, usuario_id: int, numero: int) -> M | None:
        return self._consulta(usuario_id).filter(self.modelo.numero == numero).first()

    def contar(self, usuario_id: int, **filtros) -> int:
        consulta = self._consulta(usuario_id)
        for campo, valor in filtros.items():
            consulta = consulta.filter(getattr(self.modelo, campo) == valor)
        return consulta.count()

    def _siguiente_numero(self, usuario_id: int) -> int:
        ultimo = (
            self.db.query(func.max(self.modelo.numero))
            .filter(self.modelo.usuario_id == usuario_id)
            .scalar()
        )
        return (ultimo or 0) + 1

    def crear(self, usuario_id: int, datos: dict) -> M:
        """Inserta el registro con el siguiente número del usuario.

        Si dos peticiones llegan al mismo tiempo y calculan el mismo número,
        la restricción UNIQUE(usuario_id, numero) rechaza una; se reintenta.
        """
        for intento in range(3):
            obj = self.modelo(usuario_id=usuario_id, numero=self._siguiente_numero(usuario_id), **datos)
            self.db.add(obj)
            try:
                self.db.commit()
                self.db.refresh(obj)
                return obj
            except IntegrityError:
                self.db.rollback()
                if intento == 2:
                    raise
        raise RuntimeError("inalcanzable")

    def actualizar(self, obj: M, cambios: dict) -> M:
        for campo, valor in cambios.items():
            setattr(obj, campo, valor)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def eliminar(self, obj: M) -> None:
        self.db.delete(obj)
        self.db.commit()
