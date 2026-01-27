from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET: LISTAR TODOS LOS USUARIOS
# ============================================================
@router.get("/", response_model=list[schemas.UsuarioOut])
def get_usuarios(db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()


# ============================================================
# GET: USUARIOS POR SEDE
# ============================================================
@router.get("/sede/{sede_id}", response_model=list[schemas.UsuarioOut])
def get_usuarios_por_sede(sede_id: str, db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).filter(models.Usuario.sede_id == sede_id).all()
    return usuarios


# ============================================================
# GET: USUARIOS POR EMPRESA
# ============================================================
@router.get("/empresa/{empresa_id}", response_model=list[schemas.UsuarioOut])
def get_usuarios_por_empresa(empresa_id: str, db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).filter(models.Usuario.empresa_id == empresa_id).all()
    return usuarios


# ============================================================
# GET: USUARIO POR ID
# ============================================================
@router.get("/{usuario_id}", response_model=schemas.UsuarioOut)
def get_usuario(usuario_id: str, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


# ============================================================
# POST: CREAR USUARIO
# ============================================================
@router.post("/", response_model=schemas.UsuarioOut)
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):

    # Validar username único
    if db.query(models.Usuario).filter(models.Usuario.username == usuario.username).first():
        raise HTTPException(status_code=400, detail="El username ya está en uso")

    nuevo = models.Usuario(**usuario.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# ============================================================
# PUT: ACTUALIZAR USUARIO
# ============================================================
@router.put("/{usuario_id}", response_model=schemas.UsuarioOut)
def actualizar_usuario(usuario_id: str, datos: schemas.UsuarioBase, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for key, value in datos.dict().items():
        setattr(usuario, key, value)

    db.commit()
    db.refresh(usuario)
    return usuario


# ============================================================
# DELETE: ELIMINAR USUARIO
# ============================================================
@router.delete("/{usuario_id}")
def eliminar_usuario(usuario_id: str, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db.delete(usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado correctamente"}
