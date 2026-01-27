from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/locaciones", tags=["Locaciones"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET: LISTAR TODAS LAS LOCACIONES
# ============================================================

@router.get("/", response_model=list[schemas.LocacionOut])
def get_locaciones(db: Session = Depends(get_db)):
    return db.query(models.Locacion).all()


# ============================================================
# GET: OBTENER LOCACION POR ID
# ============================================================

@router.get("/{locacion_id}", response_model=schemas.LocacionOut)
def get_locacion(locacion_id: str, db: Session = Depends(get_db)):
    locacion = db.query(models.Locacion).filter(models.Locacion.id == locacion_id).first()
    if not locacion:
        raise HTTPException(status_code=404, detail="Locación no encontrada")
    return locacion


# ============================================================
# GET: LOCACIONES POR SEDE
# ============================================================

@router.get("/sede/{sede_id}", response_model=list[schemas.LocacionOut])
def get_locaciones_por_sede(sede_id: str, db: Session = Depends(get_db)):
    return db.query(models.Locacion).filter(models.Locacion.sede_id == sede_id).all()


# ============================================================
# POST: CREAR LOCACION
# ============================================================

@router.post("/", response_model=schemas.LocacionOut)
def crear_locacion(locacion: schemas.LocacionCreate, db: Session = Depends(get_db)):

    # Validar sede existente
    sede = db.query(models.Sede).filter(models.Sede.id == locacion.sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")

    nueva = models.Locacion(**locacion.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


# ============================================================
# PUT: ACTUALIZAR LOCACION
# ============================================================

@router.put("/{locacion_id}", response_model=schemas.LocacionOut)
def actualizar_locacion(locacion_id: str, datos: schemas.LocacionBase, db: Session = Depends(get_db)):
    locacion = db.query(models.Locacion).filter(models.Locacion.id == locacion_id).first()
    if not locacion:
        raise HTTPException(status_code=404, detail="Locación no encontrada")

    for key, value in datos.dict().items():
        setattr(locacion, key, value)

    db.commit()
    db.refresh(locacion)
    return locacion


# ============================================================
# DELETE: ELIMINAR LOCACION
# ============================================================

@router.delete("/{locacion_id}")
def eliminar_locacion(locacion_id: str, db: Session = Depends(get_db)):
    locacion = db.query(models.Locacion).filter(models.Locacion.id == locacion_id).first()
    if not locacion:
        raise HTTPException(status_code=404, detail="Locación no encontrada")

    db.delete(locacion)
    db.commit()
    return {"mensaje": "Locación eliminada correctamente"}
