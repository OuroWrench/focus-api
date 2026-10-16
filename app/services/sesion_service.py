from app.models._comun import ahora
from app.services.base import ServicioPorUsuario


class SesionService(ServicioPorUsuario):
    no_encontrado = "No existe la sesión de foco {numero} para este usuario"
    campos_anulables = {"fin"}

    def preparar_actualizacion(self, usuario_id: int, sesion, cambios: dict) -> dict:
        # Al marcarla como completada (o cerrarla) se registra la hora de fin.
        if "completada" in cambios and "fin" not in cambios and sesion.fin is None:
            cambios["fin"] = ahora()
        return cambios
