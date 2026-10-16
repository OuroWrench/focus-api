"""Errores de negocio. main.py los convierte en respuestas HTTP (404, 409)."""


class NoEncontrado(Exception):
    """El recurso no existe para este usuario -> 404."""


class Conflicto(Exception):
    """La operación choca con datos existentes -> 409."""
