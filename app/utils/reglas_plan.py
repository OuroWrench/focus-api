"""
Reglas "difusas" del ajuste semanal del plan de Focus!.

La adherencia (0 a 1) indica qué tanto respetó el usuario su meta de la semana.
Según la adherencia se decide cuánto cambia el límite la semana siguiente:
si cumplió bien, se reduce más; si le costó, se mantiene o se relaja un poco.
La Azure Function (serverless/function_app.py) usa exactamente estas reglas.
"""

REGLAS = [
    # (adherencia mínima, cambio %, nivel)
    (0.90, -10.0, "excelente"),
    (0.75, -5.0, "buena"),
    (0.50, 0.0, "regular"),
    (0.00, 5.0, "baja"),
]


def calcular_cambio(adherencia: float) -> tuple[float, str]:
    for minimo, cambio, nivel in REGLAS:
        if adherencia >= minimo:
            return cambio, nivel
    return REGLAS[-1][1], REGLAS[-1][2]
