from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import SessionLocal
from .. import models, schemas
import uuid
import secrets

router = APIRouter(prefix="/citas", tags=["Citas"])

# ============================================================
# DB SESSION
# ============================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# AGENDAR CITA
# ============================================================

@router.post("/agendar", response_model=schemas.CitaOut)
def agendar_cita(data: schemas.CitaCreate, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    servicio = db.query(models.Servicio).filter(models.Servicio.id == data.servicio_id).first()
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    # Verificar conflicto de horario
    conflicto = db.query(models.Cita).filter(
        models.Cita.cliente_id == data.cliente_id,
        models.Cita.sede_id == data.sede_id,
        models.Cita.fecha == data.fecha,
        models.Cita.hora == data.hora,
        models.Cita.estado.in_(["agendada", "check_in", "en_espera"])
    ).first()
    if conflicto:
        raise HTTPException(status_code=400, detail="Ya tienes una cita en ese horario")

    qr_token = data.qr_token or secrets.token_urlsafe(16)

    cita = models.Cita(
        id=data.id or str(uuid.uuid4()),
        cliente_id=data.cliente_id,
        servicio_id=data.servicio_id,
        sede_id=data.sede_id,
        calendario_id=data.calendario_id,
        fecha=data.fecha,
        hora=data.hora,
        estado="agendada",
        notas=data.notas,
        qr_token=qr_token,
    )

    db.add(cita)
    db.commit()
    db.refresh(cita)

    result = cita.__dict__.copy()
    result["servicio_nombre"] = servicio.nombre
    result["cliente_nombre"] = cliente.nombre

    return result

# ============================================================
# OBTENER CITAS DE UN CLIENTE
# ============================================================

@router.get("/cliente/{cliente_id}", response_model=list[schemas.CitaOut])
def get_citas_cliente(cliente_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Cita, models.Servicio.nombre.label("servicio_nombre"), models.Cliente.nombre.label("cliente_nombre"))
        .join(models.Servicio, models.Cita.servicio_id == models.Servicio.id)
        .join(models.Cliente, models.Cita.cliente_id == models.Cliente.id)
        .filter(models.Cita.cliente_id == cliente_id)
        .order_by(models.Cita.fecha.asc(), models.Cita.hora.asc())
        .all()
    )

    resultado = []
    for cita, servicio_nombre, cliente_nombre in rows:
        data = cita.__dict__.copy()
        data["servicio_nombre"] = servicio_nombre
        data["cliente_nombre"] = cliente_nombre
        resultado.append(data)

    return resultado

# ============================================================
# OBTENER CITAS DE HOY PARA UN CLIENTE EN UNA SEDE (KIOSCO)
# ============================================================

@router.get("/hoy/{cliente_id}/{sede_id}", response_model=list[schemas.CitaOut])
def get_citas_hoy_kiosco(cliente_id: str, sede_id: str, db: Session = Depends(get_db)):
    from datetime import date
    hoy = date.today().isoformat()
    rows = (
        db.query(models.Cita, models.Servicio.nombre.label("servicio_nombre"), models.Cliente.nombre.label("cliente_nombre"))
        .join(models.Servicio, models.Cita.servicio_id == models.Servicio.id)
        .join(models.Cliente, models.Cita.cliente_id == models.Cliente.id)
        .filter(
            models.Cita.cliente_id == cliente_id,
            models.Cita.sede_id == sede_id,
            models.Cita.fecha == hoy,
            models.Cita.estado == "agendada"
        )
        .order_by(models.Cita.hora.asc())
        .all()
    )

    resultado = []
    for cita, servicio_nombre, cliente_nombre in rows:
        data = cita.__dict__.copy()
        data["servicio_nombre"] = servicio_nombre
        data["cliente_nombre"] = cliente_nombre
        resultado.append(data)

    return resultado

# ============================================================
# OBTENER CITAS DE UNA SEDE POR FECHA
# ============================================================

@router.get("/sede/{sede_id}/fecha/{fecha}", response_model=list[schemas.CitaOut])
def get_citas_sede_fecha(sede_id: str, fecha: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Cita, models.Servicio.nombre.label("servicio_nombre"), models.Cliente.nombre.label("cliente_nombre"))
        .join(models.Servicio, models.Cita.servicio_id == models.Servicio.id)
        .join(models.Cliente, models.Cita.cliente_id == models.Cliente.id)
        .filter(
            models.Cita.sede_id == sede_id,
            models.Cita.fecha == fecha
        )
        .order_by(models.Cita.hora.asc())
        .all()
    )

    resultado = []
    for cita, servicio_nombre, cliente_nombre in rows:
        data = cita.__dict__.copy()
        data["servicio_nombre"] = servicio_nombre
        data["cliente_nombre"] = cliente_nombre
        resultado.append(data)

    return resultado

# ============================================================
# CHECK-IN POR APP
# ============================================================

@router.put("/checkin/app/{cita_id}", response_model=schemas.CitaOut)
def checkin_app(cita_id: str, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.estado != "agendada":
        raise HTTPException(status_code=400, detail=f"La cita está en estado '{cita.estado}', no se puede hacer check-in")

    return _procesar_checkin(cita, metodo="app", db=db)

# ============================================================
# CHECK-IN POR QR
# ============================================================

@router.put("/checkin/qr/{qr_token}", response_model=schemas.CitaOut)
def checkin_qr(qr_token: str, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.qr_token == qr_token).first()
    if not cita:
        raise HTTPException(status_code=404, detail="QR inválido o cita no encontrada")

    if cita.estado != "agendada":
        raise HTTPException(status_code=400, detail=f"La cita está en estado '{cita.estado}', no se puede hacer check-in")

    return _procesar_checkin(cita, metodo="qr", db=db)

# ============================================================
# LÓGICA INTERNA DE CHECK-IN
# ============================================================

def _procesar_checkin(cita: models.Cita, metodo: str, db: Session):
    ahora = datetime.utcnow()
    hora_cita = datetime.strptime(f"{cita.fecha} {cita.hora}", "%Y-%m-%d %H:%M") - timedelta(hours=1)
    ventana_inicio = hora_cita - timedelta(minutes=20)
    ventana_fin = hora_cita + timedelta(minutes=20)

    if not (ventana_inicio <= ahora <= ventana_fin):
        raise HTTPException(
            status_code=400,
            detail=f"Check-in solo permitido entre {ventana_inicio.strftime('%H:%M')} y {ventana_fin.strftime('%H:%M')}"
        )

    servicio = db.query(models.Servicio).filter(models.Servicio.id == cita.servicio_id).first()
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cita.cliente_id).first()

    hoy = ahora.date()
    ultima_fecha = None
    if servicio.ultima_generacion:
        if isinstance(servicio.ultima_generacion, datetime):
            ultima_fecha = servicio.ultima_generacion.date()

    if ultima_fecha is None or ultima_fecha != hoy:
        servicio.contador_actual = servicio.rango_inicio
        servicio.ultima_generacion = ahora

    codigo = f"{servicio.identificador_letra}-{servicio.contador_actual}"

    ticket = models.Ticket(
        id=str(uuid.uuid4()),
        codigo=codigo,
        servicio_id=cita.servicio_id,
        estado="pendiente",
        sede_id=cita.sede_id,
        cliente_id=cita.cliente_id,
        cita_id=cita.id,
        notas=cita.notas,
    )

    servicio.contador_actual += 1
    if servicio.contador_actual > servicio.rango_fin:
        servicio.contador_actual = servicio.rango_inicio

    db.add(ticket)
    db.flush()

    cita.estado = "check_in"
    cita.metodo_checkin = metodo
    cita.hora_checkin = ahora
    cita.ticket_id = ticket.id

    db.commit()
    db.refresh(cita)

    result = cita.__dict__.copy()
    result["servicio_nombre"] = servicio.nombre
    result["cliente_nombre"] = cliente.nombre

    return result

# ============================================================
# REAGENDAR CITA
# ============================================================

@router.put("/reagendar/{cita_id}", response_model=schemas.CitaOut)
def reagendar_cita(cita_id: str, data: schemas.CitaReagendar, db: Session = Depends(get_db)):
    cita_original = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita_original:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita_original.estado not in ["agendada"]:
        raise HTTPException(status_code=400, detail="Solo se pueden reagendar citas en estado 'agendada'")

    # Cancelar la cita original
    cita_original.estado = "cancelada"

    # Crear la nueva cita
    nueva_cita = models.Cita(
        id=str(uuid.uuid4()),
        cliente_id=cita_original.cliente_id,
        servicio_id=cita_original.servicio_id,
        sede_id=cita_original.sede_id,
        calendario_id=data.calendario_id,
        fecha=data.nueva_fecha,
        hora=data.nueva_hora,
        estado="agendada",
        notas=cita_original.notas,
        qr_token=secrets.token_urlsafe(16),
        cita_original_id=cita_original.id,
    )

    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)

    servicio = db.query(models.Servicio).filter(models.Servicio.id == nueva_cita.servicio_id).first()
    cliente = db.query(models.Cliente).filter(models.Cliente.id == nueva_cita.cliente_id).first()

    result = nueva_cita.__dict__.copy()
    result["servicio_nombre"] = servicio.nombre
    result["cliente_nombre"] = cliente.nombre

    return result

# ============================================================
# CANCELAR CITA
# ============================================================

@router.put("/cancelar/{cita_id}", response_model=schemas.CitaOut)
def cancelar_cita(cita_id: str, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    if cita.estado not in ["agendada"]:
        raise HTTPException(status_code=400, detail=f"No se puede cancelar una cita en estado '{cita.estado}'")

    cita.estado = "cancelada"
    db.commit()
    db.refresh(cita)

    servicio = db.query(models.Servicio).filter(models.Servicio.id == cita.servicio_id).first()
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cita.cliente_id).first()

    result = cita.__dict__.copy()
    result["servicio_nombre"] = servicio.nombre
    result["cliente_nombre"] = cliente.nombre

    return result

# ============================================================
# MARCAR NO ASISTIO (para operadores)
# ============================================================

@router.put("/no-asistio/{cita_id}", response_model=schemas.CitaOut)
def no_asistio(cita_id: str, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    cita.estado = "no_asistio"
    db.commit()
    db.refresh(cita)

    servicio = db.query(models.Servicio).filter(models.Servicio.id == cita.servicio_id).first()
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cita.cliente_id).first()

    result = cita.__dict__.copy()
    result["servicio_nombre"] = servicio.nombre
    result["cliente_nombre"] = cliente.nombre

    return result

# ============================================================
# OBTENER CITA POR ID
# ============================================================

@router.get("/{cita_id}", response_model=schemas.CitaOut)
def get_cita(cita_id: str, db: Session = Depends(get_db)):
    row = (
        db.query(models.Cita, models.Servicio.nombre.label("servicio_nombre"), models.Cliente.nombre.label("cliente_nombre"))
        .join(models.Servicio, models.Cita.servicio_id == models.Servicio.id)
        .join(models.Cliente, models.Cita.cliente_id == models.Cliente.id)
        .filter(models.Cita.id == cita_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    cita, servicio_nombre, cliente_nombre = row
    result = cita.__dict__.copy()
    result["servicio_nombre"] = servicio_nombre
    result["cliente_nombre"] = cliente_nombre

    return result
