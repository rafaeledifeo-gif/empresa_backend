from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from app.database import get_db
from app.models import Cliente
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# ============================================================
# SCHEMAS
# ============================================================

class ClienteCreate(BaseModel):
    nombre: str
    email: Optional[str] = None
    password: Optional[str] = None
    numero_identificacion: Optional[str] = None

class ClienteLogin(BaseModel):
    email: str
    password: str

class ClienteOut(BaseModel):
    id: str
    nombre: str
    email: Optional[str] = None
    numero_identificacion: Optional[str] = None

    class Config:
        from_attributes = True

# ============================================================
# POST: Crear cliente (desde app móvil u operador)
# ============================================================

@router.post("/clientes", response_model=ClienteOut)
def crear_cliente(data: ClienteCreate, db: Session = Depends(get_db)):
    # Verificar duplicado por email
    if data.email:
        if db.query(Cliente).filter_by(email=data.email).first():
            raise HTTPException(status_code=400, detail="Email ya registrado")

    # Verificar duplicado por número de identificación
    if data.numero_identificacion:
        if db.query(Cliente).filter_by(
            numero_identificacion=data.numero_identificacion
        ).first():
            raise HTTPException(
                status_code=400,
                detail="Ya existe un cliente con ese número de identificación"
            )

    nuevo = Cliente(
        id=str(uuid4()),
        nombre=data.nombre,
        email=data.email,
        numero_identificacion=data.numero_identificacion,
        hashed_password=hash_password(data.password) if data.password else "",
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ============================================================
# GET: Buscar cliente por número de identificación
# ============================================================

@router.get("/clientes/buscar/{numero_identificacion}", response_model=ClienteOut)
def buscar_cliente(numero_identificacion: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(
        numero_identificacion=numero_identificacion
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# ============================================================
# GET: Buscar cliente por email
# ============================================================

@router.get("/clientes/buscar-email/{email}", response_model=ClienteOut)
def buscar_cliente_email(email: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(email=email).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# ============================================================
# GET: Obtener cliente por ID
# ============================================================

@router.get("/clientes/{cliente_id}", response_model=ClienteOut)
def get_cliente(cliente_id: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

# ============================================================
# POST: Login cliente (app móvil)
# ============================================================

@router.post("/login", response_model=ClienteOut)
def login_cliente(data: ClienteLogin, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(email=data.email).first()
    if not cliente or not verify_password(data.password, cliente.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return cliente