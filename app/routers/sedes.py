from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/sedes", tags=["Sedes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET: LISTAR TODAS LAS SEDES
# ============================================================

@router.get("/", response_model=list[schemas.SedeOut])
def get_sedes(db: Session = Depends(get_db)):
    return db.query(models.Sede).all()


# ============================================================
# GET: OBTENER SEDE POR ID
# ============================================================

@router.get("/{sede_id}", response_model=schemas.SedeOut)
def get_sede(sede_id: str, db: Session = Depends(get_db)):
    sede = db.query(models.Sede).filter(models.Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return sede


# ============================================================
# GET: LISTAR SEDES POR EMPRESA
# ============================================================

@router.get("/empresa/{empresa_id}", response_model=list[schemas.SedeOut])
def get_sedes_por_empresa(empresa_id: str, db: Session = Depends(get_db)):
    return db.query(models.Sede).filter(models.Sede.empresa_id == empresa_id).all()


# ============================================================
# POST: CREAR SEDE
# ============================================================

@router.post("/", response_model=schemas.SedeOut)
def crear_sede(sede: schemas.SedeCreate, db: Session = Depends(get_db)):

    # Validar empresa existente
    empresa = db.query(models.Empresa).filter(models.Empresa.id == sede.empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    nueva = models.Sede(**sede.dict())
    db.add(nueva)

    # Actualizar contador de sedes en Empresa
    empresa.cantidad_sedes += 1

    db.commit()
    db.refresh(nueva)
    return nueva


# ============================================================
# PUT: ACTUALIZAR SEDE
# ============================================================

@router.put("/{sede_id}", response_model=schemas.SedeOut)
def actualizar_sede(sede_id: str, datos: schemas.SedeUpdate, db: Session = Depends(get_db)):
    sede = db.query(models.Sede).filter(models.Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")

    for key, value in datos.dict().items():
        setattr(sede, key, value)

    db.commit()
    db.refresh(sede)
    return sede


# ============================================================
# DELETE: ELIMINAR SEDE
# ============================================================

@router.delete("/{sede_id}")
def eliminar_sede(sede_id: str, db: Session = Depends(get_db)):
    sede = db.query(models.Sede).filter(models.Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")

    empresa = db.query(models.Empresa).filter(models.Empresa.id == sede.empresa_id).first()
    if empresa:
        empresa.cantidad_sedes -= 1

    db.delete(sede)
    db.commit()
    return {"mensaje": "Sede eliminada correctamente"}
