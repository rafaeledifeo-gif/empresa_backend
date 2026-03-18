from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/servicios", tags=["Servicios"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# GET: LISTAR SERVICIOS (con filtro opcional por sede_id)
# ============================================================

@router.get("/", response_model=list[schemas.ServicioOut])
def get_servicios(sede_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Servicio)
    if sede_id:
        query = query.filter(models.Servicio.sede_id == sede_id)
    return query.all()

# ============================================================
# GET: LISTAR SERVICIOS POR SEDE
# ============================================================

@router.get("/sede/{sede_id}", response_model=list[schemas.ServicioOut])
def get_servicios_por_sede(sede_id: str, db: Session = Depends(get_db)):
    return db.query(models.Servicio).filter(models.Servicio.sede_id == sede_id).all()

# ============================================================
# POST: CREAR SERVICIO
# ============================================================

@router.post("/", response_model=schemas.ServicioOut)
def crear_servicio(servicio: schemas.ServicioCreate, db: Session = Depends(get_db)):

    if servicio.rango_inicio < 1 or servicio.rango_inicio > 999:
        raise HTTPException(status_code=400, detail="rango_inicio debe estar entre 1 y 999")

    if servicio.rango_fin < 1 or servicio.rango_fin > 999:
        raise HTTPException(status_code=400, detail="rango_fin debe estar entre 1 y 999")

    if servicio.rango_inicio >= servicio.rango_fin:
        raise HTTPException(status_code=400, detail="rango_inicio debe ser menor que rango_fin")

    nuevo = models.Servicio(
        id=servicio.id,
        nombre=servicio.nombre,
        descripcion=servicio.descripcion,
        sede_id=servicio.sede_id,
        identificador_letra=servicio.identificador_letra,
        rango_inicio=servicio.rango_inicio,
        rango_fin=servicio.rango_fin,
        contador_actual=servicio.rango_inicio,
        ultima_generacion=datetime.now(),
        activo=True,
        tipo_servicio=servicio.tipo_servicio or "directo",
        calendario_id=servicio.calendario_id,
        modalidad=servicio.modalidad or "presencial",
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

# ============================================================
# PUT: ACTUALIZAR SERVICIO COMPLETO
# ============================================================

@router.put("/{servicio_id}", response_model=schemas.ServicioOut)
def actualizar_servicio(
    servicio_id: str,
    datos: schemas.ServicioUpdate,
    activo: bool | None = None,
    db: Session = Depends(get_db)
):
    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()

    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    # Actualizar campos
    servicio.nombre = datos.nombre
    servicio.descripcion = datos.descripcion
    servicio.identificador_letra = datos.identificador_letra
    servicio.rango_inicio = datos.rango_inicio
    servicio.rango_fin = datos.rango_fin
    servicio.tipo_servicio = datos.tipo_servicio or "directo"
    servicio.calendario_id = datos.calendario_id
    servicio.modalidad = datos.modalidad or "presencial"

    # Si viene el query param activo, también lo actualizamos
    if activo is not None:
        servicio.activo = activo

    db.commit()
    db.refresh(servicio)
    return servicio

# ============================================================
# DELETE: ELIMINAR SERVICIO
# ============================================================

@router.delete("/{servicio_id}")
def eliminar_servicio(servicio_id: str, db: Session = Depends(get_db)):
    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()

    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    db.delete(servicio)
    db.commit()
    return {"mensaje": "Servicio eliminado"}

# ============================================================
# POST: GENERAR TURNO
# ============================================================

@router.post("/{servicio_id}/generar_turno", response_model=schemas.TurnoResponse)
def generar_turno(servicio_id: str, db: Session = Depends(get_db)):

    servicio = db.query(models.Servicio).filter(models.Servicio.id == servicio_id).first()

    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    hoy = date.today()

    if servicio.ultima_generacion is None or servicio.ultima_generacion.date() != hoy:
        servicio.contador_actual = servicio.rango_inicio

    siguiente = servicio.contador_actual + 1

    if siguiente > servicio.rango_fin:
        siguiente = servicio.rango_inicio

    servicio.contador_actual = siguiente
    servicio.ultima_generacion = datetime.now()

    db.commit()
    db.refresh(servicio)

    numero_formateado = f"{siguiente:03d}"
    turno_final = f"{servicio.identificador_letra}{numero_formateado}"

    return schemas.TurnoResponse(
        turno=turno_final,
        numero=siguiente,
        letra=servicio.identificador_letra
    )