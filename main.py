# main.py — Focus! API (FastAPI + SQLAlchemy)
import os
from datetime import datetime, date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./focus.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ---------------- MODELOS ----------------
class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    nombre = Column(String)
    password_hash = Column(String)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    seudonimo = Column(String, nullable=True)
    activo = Column(Boolean, default=True)
    apps = relationship("App", back_populates="usuario")

class App(Base):
    __tablename__ = "app"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    nombre = Column(String)
    paquete = Column(String)
    categoria = Column(String)
    limite_aperturas = Column(Integer)
    usuario = relationship("Usuario", back_populates="apps")

class Franja(Base):
    __tablename__ = "franja"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    hora_inicio = Column(String)
    hora_fin = Column(String)

class EventoUso(Base):
    __tablename__ = "evento_uso"
    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("app.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    inicio = Column(DateTime)
    fin = Column(DateTime)
    duracion_seg = Column(Integer)
    franja_id = Column(Integer, ForeignKey("franja.id"))

class Plan(Base):
    __tablename__ = "plan"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    fecha_inicio = Column(Date)
    limite_base = Column(Integer)
    semana_actual = Column(Integer, default=1)
    activo = Column(Boolean, default=True)
    ajustes = relationship("AjustePlan", back_populates="plan")

class AjustePlan(Base):
    __tablename__ = "ajuste_plan"
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plan.id"))
    semana = Column(Integer)
    uso_meta = Column(Float)
    adherencia = Column(Float)
    cambio_pct = Column(Float)
    fecha = Column(Date, default=date.today)
    plan = relationship("Plan", back_populates="ajustes")

class Pausa(Base):
    __tablename__ = "pausa"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    app_id = Column(Integer, ForeignKey("app.id"))
    tipo = Column(String)
    duracion_seg = Column(Integer)
    ignorada = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.utcnow)

class DominioBloqueado(Base):
    __tablename__ = "dominio_bloqueado"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    dominio = Column(String)
    activo = Column(Boolean, default=True)

class SesionFoco(Base):
    __tablename__ = "sesion_foco"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    inicio = Column(DateTime, default=datetime.utcnow)
    fin = Column(DateTime, nullable=True)
    duracion_min = Column(Integer)
    completada = Column(Boolean, default=False)

# Sincronizar esquema desde el servidor
Base.metadata.create_all(bind=engine)

# ---------------- SCHEMAS ----------------
class UsuarioIn(BaseModel):
    email: str; nombre: str; password: str
class UsuarioOut(BaseModel):
    id: int; email: str; nombre: str; activo: bool
    class Config: from_attributes = True
class LoginIn(BaseModel):
    email: str; password: str
class AppIn(BaseModel):
    nombre: str; paquete: str; categoria: str; limite_aperturas: int
class AppOut(AppIn):
    id: int
    class Config: from_attributes = True
class EventoIn(BaseModel):
    app_id: int; inicio: datetime; fin: datetime; duracion_seg: int; franja_id: int
class EventoOut(EventoIn):
    id: int
    class Config: from_attributes = True
class PlanIn(BaseModel):
    fecha_inicio: date; limite_base: int
class AjusteIn(BaseModel):
    semana: int; uso_meta: float; adherencia: float; cambio_pct: float
class PausaIn(BaseModel):
    app_id: int; tipo: str; duracion_seg: int; ignorada: bool = False
class DominioIn(BaseModel):
    dominio: str
class SesionIn(BaseModel):
    duracion_min: int

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

app = FastAPI(title="Focus! API", version="1.0.0")

# ---------------- RUTAS ----------------
@app.get("/salud")
def salud(): return {"status": "ok"}

@app.post("/auth/registro", status_code=201)
def registro(u: UsuarioIn, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(Usuario.email == u.email).first()
    if existe: raise HTTPException(400, "Email ya registrado")
    nuevo = Usuario(email=u.email, nombre=u.nombre, password_hash=u.password)
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    return {"id": nuevo.id, "token": f"token-{nuevo.id}"}

@app.post("/auth/login")
def login(l: LoginIn, db: Session = Depends(get_db)):
    u = db.query(Usuario).filter(Usuario.email == l.email, Usuario.password_hash == l.password).first()
    if not u: raise HTTPException(401, "Credenciales incorrectas")
    return {"token": f"token-{u.id}"}

@app.get("/usuarios/{id}", response_model=UsuarioOut)
def get_usuario(id: int, db: Session = Depends(get_db)):
    u = db.get(Usuario, id)
    if not u: raise HTTPException(404, "No encontrado")
    return u

@app.put("/usuarios/{id}")
def update_usuario(id: int, nombre: str, db: Session = Depends(get_db)):
    u = db.get(Usuario, id)
    if not u: raise HTTPException(404, "No encontrado")
    u.nombre = nombre; db.commit(); return {"ok": True}

@app.delete("/usuarios/{id}", status_code=204)
def delete_usuario(id: int, db: Session = Depends(get_db)):
    u = db.get(Usuario, id)
    if not u: raise HTTPException(404, "No encontrado")
    u.activo = False; db.commit()

@app.post("/apps", status_code=201, response_model=AppOut)
def crear_app(a: AppIn, usuario_id: int = 1, db: Session = Depends(get_db)):
    nueva = App(usuario_id=usuario_id, **a.dict())
    db.add(nueva); db.commit(); db.refresh(nueva); return nueva

@app.get("/apps", response_model=List[AppOut])
def listar_apps(db: Session = Depends(get_db)): return db.query(App).all()

@app.put("/apps/{id}")
def update_app(id: int, limite_aperturas: int, db: Session = Depends(get_db)):
    a = db.get(App, id)
    if not a: raise HTTPException(404, "No encontrada")
    a.limite_aperturas = limite_aperturas; db.commit(); return {"ok": True}

@app.delete("/apps/{id}", status_code=204)
def delete_app(id: int, db: Session = Depends(get_db)):
    a = db.get(App, id)
    if not a: raise HTTPException(404, "No encontrada")
    db.delete(a); db.commit()

@app.post("/eventos", status_code=201, response_model=EventoOut)
def crear_evento(e: EventoIn, usuario_id: int = 1, db: Session = Depends(get_db)):
    nuevo = EventoUso(usuario_id=usuario_id, **e.dict())
    db.add(nuevo); db.commit(); db.refresh(nuevo); return nuevo

@app.get("/eventos", response_model=List[EventoOut])
def listar_eventos(franja_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(EventoUso)
    if franja_id: q = q.filter(EventoUso.franja_id == franja_id)
    return q.all()

@app.get("/franjas")
def listar_franjas(db: Session = Depends(get_db)): return db.query(Franja).all()

@app.post("/planes", status_code=201)
def crear_plan(pl: PlanIn, usuario_id: int = 1, db: Session = Depends(get_db)):
    nuevo = Plan(usuario_id=usuario_id, **pl.dict())
    db.add(nuevo); db.commit(); db.refresh(nuevo); return {"id": nuevo.id}

@app.get("/planes/activo")
def plan_activo(db: Session = Depends(get_db)):
    pl = db.query(Plan).filter(Plan.activo == True).first()
    if not pl: raise HTTPException(404, "Sin plan activo")
    return {"id": pl.id, "limite_base": pl.limite_base, "semana_actual": pl.semana_actual}

@app.post("/planes/{id}/ajustes", status_code=201)
def ajuste(id: int, a: AjusteIn, db: Session = Depends(get_db)):
    pl = db.get(Plan, id)
    if not pl: raise HTTPException(404, "Plan no encontrado")
    nuevo = AjustePlan(plan_id=id, **a.dict())
    db.add(nuevo); db.commit(); return {"ok": True, "cambio_pct": a.cambio_pct}

@app.post("/pausas", status_code=201)
def registrar_pausa(pa: PausaIn, usuario_id: int = 1, db: Session = Depends(get_db)):
    nueva = Pausa(usuario_id=usuario_id, **pa.dict())
    db.add(nueva); db.commit(); db.refresh(nueva); return {"id": nueva.id}

@app.get("/pausas")
def historial_pausas(db: Session = Depends(get_db)): return db.query(Pausa).all()

@app.post("/dominios", status_code=201)
def agregar_dominio(d: DominioIn, usuario_id: int = 1, db: Session = Depends(get_db)):
    nuevo = DominioBloqueado(usuario_id=usuario_id, dominio=d.dominio)
    db.add(nuevo); db.commit(); db.refresh(nuevo); return {"id": nuevo.id}

@app.get("/dominios")
def listar_dominios(db: Session = Depends(get_db)): return db.query(DominioBloqueado).all()

@app.delete("/dominios/{id}", status_code=204)
def eliminar_dominio(id: int, db: Session = Depends(get_db)):
    d = db.get(DominioBloqueado, id)
    if not d: raise HTTPException(404, "No encontrado")
    db.delete(d); db.commit()

@app.post("/sesiones-foco", status_code=201)
def iniciar_sesion(s: SesionIn, usuario_id: int = 1, db: Session = Depends(get_db)):
    nueva = SesionFoco(usuario_id=usuario_id, duracion_min=s.duracion_min)
    db.add(nueva); db.commit(); db.refresh(nueva); return {"id": nueva.id}

@app.put("/sesiones-foco/{id}")
def cerrar_sesion(id: int, completada: bool = True, db: Session = Depends(get_db)):
    s = db.get(SesionFoco, id)
    if not s: raise HTTPException(404, "No encontrada")
    s.fin = datetime.utcnow(); s.completada = completada; db.commit(); return {"ok": True}

@app.get("/estadisticas")
def estadisticas(db: Session = Depends(get_db)):
    return {
        "total_eventos": db.query(EventoUso).count(),
        "total_apps": db.query(App).count(),
        "pausas_ignoradas": db.query(Pausa).filter(Pausa.ignorada == True).count(),
        "sesiones_foco_completadas": db.query(SesionFoco).filter(SesionFoco.completada == True).count(),
    }
