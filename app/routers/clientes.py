from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import bcrypt
import uuid

from ..database import get_db
from .. import models

router = APIRouter(tags=["Clientes"])

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
}

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

class ClienteCreate(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    email: Optional[str] = None
    password: str
    numero_identificacion: Optional[str] = None

class ClienteOut(BaseModel):
    id: str
    nombre: str
    apellido: Optional[str] = None
    email: Optional[str] = None
    numero_identificacion: Optional[str] = None
    class Config:
        from_attributes = True

class ClienteLogin(BaseModel):
    email: Optional[str] = None
    numero_identificacion: Optional[str] = None
    password: str

def cliente_json(c):
    return {
        "id": c.id,
        "nombre": c.nombre,
        "apellido": getattr(c, 'apellido', None),
        "email": c.email,
        "numero_identificacion": c.numero_identificacion,
    }

@router.post("/clientes/")
def registrar_cliente(data: ClienteCreate, db: Session = Depends(get_db)):
    if data.email:
        if db.query(models.Cliente).filter_by(email=data.email).first():
            raise HTTPException(status_code=400, detail="Ya existe un cliente con ese email")
    if data.numero_identificacion:
        if db.query(models.Cliente).filter_by(numero_identificacion=data.numero_identificacion).first():
            raise HTTPException(status_code=400, detail="Ya existe un cliente con ese número de identificación")
    nuevo = models.Cliente(
        id=str(uuid.uuid4()),
        nombre=data.nombre,
        apellido=data.apellido,
        email=data.email,
        numero_identificacion=data.numero_identificacion,
        hashed_password=hash_password(data.password),
    )
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    return JSONResponse(content=cliente_json(nuevo), headers=CORS_HEADERS)

@router.post("/login")
def login_cliente(data: ClienteLogin, db: Session = Depends(get_db)):
    cliente = None
    if data.email:
        cliente = db.query(models.Cliente).filter_by(email=data.email).first()
    elif data.numero_identificacion:
        cliente = db.query(models.Cliente).filter_by(numero_identificacion=data.numero_identificacion).first()
    else:
        raise HTTPException(status_code=400, detail="Proporciona email o número de identificación")
    if not cliente or not verify_password(data.password, cliente.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return JSONResponse(content=cliente_json(cliente), headers=CORS_HEADERS)

@router.get("/clientes/buscar/{numero_identificacion}", response_model=ClienteOut)
def buscar_cliente(numero_identificacion: str, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter_by(numero_identificacion=numero_identificacion).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.get("/clientes/{cliente_id}", response_model=ClienteOut)
def get_cliente(cliente_id: str, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente