from datetime import date, datetime, time, timedelta

from app.repositories.franja_repository import FranjaRepository
from app.utils.errores import Conflicto, NoEncontrado


class FranjaService:
    def __init__(self, repo: FranjaRepository):
        self.repo = repo

    def listar(self, fecha: date | None):
        return self.repo.listar(fecha)

    def obtener(self, franja_id: int):
        franja = self.repo.obtener(franja_id)
        if franja is None:
            raise NoEncontrado(f"No existe la franja {franja_id}")
        return franja

    def crear(self, datos):
        if self.repo.existe(datos.fecha, datos.hora_inicio):
            raise Conflicto("Ya existe una franja con esa fecha y hora de inicio")
        return self.repo.crear(datos.model_dump())

    def generar_dia(self, fecha: date):
        """Crea las 12 franjas de 2 horas de un día (las que falten)."""
        nuevas = []
        for h in range(0, 24, 2):
            inicio = time(h, 0)
            if not self.repo.existe(fecha, inicio):
                fin = (datetime.combine(fecha, inicio) + timedelta(hours=2)).time()
                nuevas.append({"fecha": fecha, "hora_inicio": inicio, "hora_fin": fin})
        if nuevas:
            self.repo.crear_varias(nuevas)
        return self.repo.listar(fecha)

    def actualizar(self, franja_id: int, cambios):
        franja = self.obtener(franja_id)
        datos = {k: v for k, v in cambios.model_dump(exclude_unset=True).items() if v is not None}
        return self.repo.actualizar(franja, datos) if datos else franja

    def eliminar(self, franja_id: int) -> None:
        franja = self.obtener(franja_id)
        if self.repo.en_uso(franja):
            raise Conflicto("La franja tiene eventos asociados; no se puede eliminar")
        self.repo.eliminar(franja)
