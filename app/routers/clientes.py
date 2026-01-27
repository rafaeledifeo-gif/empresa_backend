from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from app.database import get_db
from app.models import Cliente
from pydantic import BaseModel
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 Seguridad
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# 📦 Esquemas Pydantic
class ClienteCreate(BaseModel):
    nombre: str
    email: str
    password: str

class ClienteLogin(BaseModel):
    email: str
    password: str

class ClienteOut(BaseModel):
    id: str
    nombre: str
    email: str

# ✅ Registro de cliente
@router.post("/clientes", response_model=ClienteOut)
def crear_cliente(data: ClienteCreate, db: Session = Depends(get_db)):
    if db.query(Cliente).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    nuevo = Cliente(
        id=str(uuid4()),
        nombre=data.nombre,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# 🔐 Login de cliente
@router.post("/login", response_model=ClienteOut)
def login_cliente(data: ClienteLogin, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter_by(email=data.email).first()
    if not cliente or not verify_password(data.password, cliente.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return cliente
