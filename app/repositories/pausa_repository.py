from app.models import Pausa
from app.repositories.base import RepositorioPorUsuario


class PausaRepository(RepositorioPorUsuario[Pausa]):
    modelo = Pausa
