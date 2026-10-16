"""
Identificación del usuario por header.

Todas las rutas privadas usan Depends(usuario_actual). El usuario viaja en el
header X-Usuario-Id y los números de las rutas son relativos a él:

    GET /pausas/7   +   X-Usuario-Id: 1   ->   la 7.ª pausa del usuario 1

Cuando se agregue JWT solo cambia esta función (leerá Authorization: Bearer);
los controladores no se tocan.
"""
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario


def usuario_actual(
    x_usuario_id: int = Header(..., alias="X-Usuario-Id", description="Id del usuario que hace la petición"),
    db: Session = Depends(get_db),
) -> Usuario:
    usuario = db.get(Usuario, x_usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no válido o inactivo")
    return usuario
