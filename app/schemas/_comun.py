from pydantic import BaseModel, ConfigDict


class Respuesta(BaseModel):
    """Base de las respuestas: permite construirlas directo desde los modelos ORM."""

    model_config = ConfigDict(from_attributes=True)
