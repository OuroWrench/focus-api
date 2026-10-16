"""
Servicio genérico para las tablas de un usuario.

Aquí van las reglas de negocio. No sabe nada de HTTP ni de SQL:
le pide cosas al repositorio y lanza NoEncontrado / Conflicto.
"""
from pydantic import BaseModel

from app.repositories.base import RepositorioPorUsuario
from app.utils.errores import NoEncontrado


class ServicioPorUsuario:
    no_encontrado = "No existe el registro {numero} para este usuario"
    campos_anulables: set[str] = set()   # campos que sí se pueden poner en null al actualizar

    def __init__(self, repo: RepositorioPorUsuario):
        self.repo = repo

    # -- ganchos que cada servicio puede sobrescribir --
    def preparar_creacion(self, usuario_id: int, datos: dict) -> dict:
        return datos

    def preparar_actualizacion(self, usuario_id: int, obj, cambios: dict) -> dict:
        return cambios

    def antes_de_eliminar(self, obj) -> None:
        pass

    # -- CRUD --
    def listar(self, usuario_id: int):
        return self.repo.listar(usuario_id)

    def obtener(self, usuario_id: int, numero: int):
        obj = self.repo.obtener(usuario_id, numero)
        if obj is None:
            raise NoEncontrado(self.no_encontrado.format(numero=numero))
        return obj

    def crear(self, usuario_id: int, datos: BaseModel):
        return self.repo.crear(usuario_id, self.preparar_creacion(usuario_id, datos.model_dump()))

    def actualizar(self, usuario_id: int, numero: int, cambios: BaseModel):
        obj = self.obtener(usuario_id, numero)
        datos = {
            k: v for k, v in cambios.model_dump(exclude_unset=True).items()
            if v is not None or k in self.campos_anulables
        }
        datos = self.preparar_actualizacion(usuario_id, obj, datos)
        return self.repo.actualizar(obj, datos) if datos else obj

    def eliminar(self, usuario_id: int, numero: int) -> None:
        obj = self.obtener(usuario_id, numero)
        self.antes_de_eliminar(obj)
        self.repo.eliminar(obj)
