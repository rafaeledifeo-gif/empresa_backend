from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/funciones", tags=["Funciones"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET: LISTAR FUNCIONES
# ============================================================

@router.get("/", response_model=list[schemas.FuncionOut])
def get_funciones(db: Session = Depends(get_db)):
    funciones = db.query(models.Funcion).all()

    resultado = []
    for f in funciones:
        resultado.append(
            schemas.FuncionOut(
                id=f.id,
                nombre=f.nombre,
                descripcion=f.descripcion,
                sede_id=f.sede_id,
                servicios=[s.id for s in f.servicios]
            )
        )
    return resultado


# ============================================================
# POST: CREAR FUNCIÓN CON SERVICIOS
# ============================================================

@router.post("/", response_model=schemas.FuncionOut)
def crear_funcion(funcion: schemas.FuncionCreate, db: Session = Depends(get_db)):

    nueva = models.Funcion(
        id=funcion.id,
        nombre=funcion.nombre,
        descripcion=funcion.descripcion,
        sede_id=funcion.sede_id,
    )

    db.add(nueva)
    db.commit()
    db.refresh(nueva)

    # Asociar servicios
    if funcion.servicios:
        servicios = db.query(models.Servicio).filter(
            models.Servicio.id.in_(funcion.servicios)
        ).all()

        nueva.servicios = servicios
        db.commit()
        db.refresh(nueva)

    return schemas.FuncionOut(
        id=nueva.id,
        nombre=nueva.nombre,
        descripcion=nueva.descripcion,
        sede_id=nueva.sede_id,
        servicios=[s.id for s in nueva.servicios]
    )


# ============================================================
# PUT: ACTUALIZAR FUNCIÓN + SERVICIOS
# ============================================================

@router.put("/{funcion_id}", response_model=schemas.FuncionOut)
def actualizar_funcion(funcion_id: str, datos: schemas.FuncionCreate, db: Session = Depends(get_db)):
    funcion = db.query(models.Funcion).filter(models.Funcion.id == funcion_id).first()

    if not funcion:
        raise HTTPException(status_code=404, detail="Función no encontrada")

    # Actualizar campos básicos
    funcion.nombre = datos.nombre
    funcion.descripcion = datos.descripcion
    funcion.sede_id = datos.sede_id

    # Actualizar servicios asociados
    servicios = db.query(models.Servicio).filter(
        models.Servicio.id.in_(datos.servicios)
    ).all()

    funcion.servicios = servicios

    db.commit()
    db.refresh(funcion)

    return schemas.FuncionOut(
        id=funcion.id,
        nombre=funcion.nombre,
        descripcion=funcion.descripcion,
        sede_id=funcion.sede_id,
        servicios=[s.id for s in funcion.servicios]
    )


# ============================================================
# DELETE: ELIMINAR FUNCIÓN + RELACIONES
# ============================================================

@router.delete("/{funcion_id}")
def eliminar_funcion(funcion_id: str, db: Session = Depends(get_db)):
    funcion = db.query(models.Funcion).filter(models.Funcion.id == funcion_id).first()

    if not funcion:
        raise HTTPException(status_code=404, detail="Función no encontrada")

    funcion.servicios = []
    db.commit()

    db.delete(funcion)
    db.commit()

    return {"mensaje": "Función eliminada"}
