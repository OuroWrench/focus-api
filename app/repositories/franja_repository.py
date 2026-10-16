from datetime import date, time

from sqlalchemy.orm import Session

from app.models import EventoUso, Franja


class FranjaRepository:
    """Las franjas son un catálogo global: se identifican por id, no por usuario."""

    def __init__(self, db: Session):
        self.db = db

    def listar(self, fecha: date | None = None) -> list[Franja]:
        consulta = self.db.query(Franja)
        if fecha is not None:
            consulta = consulta.filter(Franja.fecha == fecha)
        return consulta.order_by(Franja.fecha, Franja.hora_inicio).all()

    def obtener(self, franja_id: int) -> Franja | None:
        return self.db.get(Franja, franja_id)

    def existe(self, fecha: date, hora_inicio: time) -> bool:
        return self.db.query(Franja.id).filter(Franja.fecha == fecha, Franja.hora_inicio == hora_inicio).first() is not None

    def crear(self, datos: dict) -> Franja:
        franja = Franja(**datos)
        self.db.add(franja)
        self.db.commit()
        self.db.refresh(franja)
        return franja

    def crear_varias(self, franjas: list[dict]) -> list[Franja]:
        objetos = [Franja(**f) for f in franjas]
        self.db.add_all(objetos)
        self.db.commit()
        for o in objetos:
            self.db.refresh(o)
        return objetos

    def actualizar(self, franja: Franja, cambios: dict) -> Franja:
        for campo, valor in cambios.items():
            setattr(franja, campo, valor)
        self.db.commit()
        self.db.refresh(franja)
        return franja

    def en_uso(self, franja: Franja) -> bool:
        return self.db.query(EventoUso.id).filter(EventoUso.franja_id == franja.id).first() is not None

    def eliminar(self, franja: Franja) -> None:
        self.db.delete(franja)
        self.db.commit()
