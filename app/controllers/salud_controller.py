from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, get_db

router = APIRouter(tags=["Salud"])


@router.get("/salud")
def salud(db: Session = Depends(get_db)):
    """Verifica que la API responde y que la base de datos está conectada."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "base_datos": "ok", "motor": engine.dialect.name}
