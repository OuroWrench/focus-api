"""
Focus! — API serverless (Azure Functions, modelo de programación v2 de Python).

Ruta:  POST /api/ajuste-semanal   (también acepta GET con query string)

Calcula el ajuste semanal del plan de reducción a partir del uso real y la
meta de la semana. Usa las mismas reglas difusas que la API principal
(app/utils/reglas_plan.py), así la app Android puede previsualizar el ajuste
sin guardar nada en la base de datos.

Ejemplo:
    POST https://<function-app>.azurewebsites.net/api/ajuste-semanal
    {"uso_real_min": 230, "uso_meta_min": 210, "limite_actual_min": 240}
"""
import json
import logging

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

REGLAS = [
    # (adherencia mínima, cambio %, nivel, mensaje)
    (0.90, -10.0, "excelente", "¡Gran semana! Reducimos tu límite un 10 %."),
    (0.75, -5.0, "buena", "Vas bien. Reducimos tu límite un 5 %."),
    (0.50, 0.0, "regular", "Mantengamos el mismo límite una semana más."),
    (0.00, 5.0, "baja", "Fue una semana difícil; relajamos el límite un 5 %."),
]


def _respuesta(cuerpo: dict, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(cuerpo, ensure_ascii=False),
        status_code=status,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


def _leer_numero(datos: dict, campo: str, obligatorio: bool = True) -> float | None:
    valor = datos.get(campo)
    if valor is None:
        if obligatorio:
            raise ValueError(f"Falta el campo '{campo}'")
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"'{campo}' debe ser numérico")
    if numero < 0:
        raise ValueError(f"'{campo}' no puede ser negativo")
    return numero


def calcular_ajuste(uso_real: float, uso_meta: float, limite_actual: float | None) -> dict:
    if uso_meta <= 0:
        raise ValueError("'uso_meta_min' debe ser mayor que 0")
    # Adherencia: 1.0 si usó lo mismo o menos que la meta; baja conforme se excede.
    adherencia = 1.0 if uso_real <= uso_meta else max(0.0, 1 - (uso_real - uso_meta) / uso_meta)
    for minimo, cambio, nivel, mensaje in REGLAS:
        if adherencia >= minimo:
            break
    resultado = {
        "uso_real_min": uso_real,
        "uso_meta_min": uso_meta,
        "adherencia": round(adherencia, 3),
        "nivel": nivel,
        "cambio_pct": cambio,
        "mensaje": mensaje,
    }
    if limite_actual is not None:
        resultado["limite_actual_min"] = limite_actual
        resultado["nuevo_limite_min"] = round(limite_actual * (1 + cambio / 100))
    return resultado


@app.route(route="ajuste-semanal", methods=["GET", "POST"])
def ajuste_semanal(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Focus! ajuste-semanal: %s", req.method)
    datos = dict(req.params)
    if req.method == "POST":
        try:
            cuerpo = req.get_json()
        except ValueError:
            return _respuesta({"detail": "El cuerpo debe ser JSON válido"}, 400)
        if not isinstance(cuerpo, dict):
            return _respuesta({"detail": "El cuerpo debe ser un objeto JSON"}, 400)
        datos.update(cuerpo)
    try:
        resultado = calcular_ajuste(
            _leer_numero(datos, "uso_real_min"),
            _leer_numero(datos, "uso_meta_min"),
            _leer_numero(datos, "limite_actual_min", obligatorio=False),
        )
    except ValueError as e:
        return _respuesta({"detail": str(e)}, 400)
    return _respuesta(resultado)
