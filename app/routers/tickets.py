from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import SessionLocal
from .. import models, schemas
import uuid
import asyncio

router = APIRouter(prefix="/tickets", tags=["Tickets"])


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
# CREAR TICKET
# ============================================================
@router.post("/crear", response_model=schemas.TicketOut)
def crear_ticket(data: schemas.TicketCreate, db: Session = Depends(get_db)):
    servicio = db.query(models.Servicio).filter(models.Servicio.id == data.servicio_id).first()

    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    hoy = datetime.now().date()

    # Convertir ultima_generacion a date de forma segura
    ultima_fecha = None
    if servicio.ultima_generacion is not None:
        if isinstance(servicio.ultima_generacion, datetime):
            ultima_fecha = servicio.ultima_generacion.date()
        elif isinstance(servicio.ultima_generacion, str):
            ultima_fecha = datetime.fromisoformat(servicio.ultima_generacion).date()

    # Reinicio diario
    if ultima_fecha is None or ultima_fecha != hoy:
        servicio.contador_actual = servicio.rango_inicio
        servicio.ultima_generacion = hoy.isoformat()

    # Generar código
    codigo = f"{servicio.identificador_letra}-{servicio.contador_actual}"

    # Crear ticket
    ticket = models.Ticket(
        id=str(uuid.uuid4()),
        codigo=codigo,
        servicio_id=data.servicio_id,
        notas=data.notas,
        estado="pendiente",
        sede_id=data.sede_id,
    )

    # Incrementar contador y reiniciar si supera rango_fin
    servicio.contador_actual += 1
    if servicio.contador_actual > servicio.rango_fin:
        servicio.contador_actual = servicio.rango_inicio

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Incluir servicio_nombre
    data_out = ticket.__dict__.copy()
    data_out["servicio_nombre"] = servicio.nombre

    return data_out


# ============================================================
# OBTENER TICKETS POR SEDE
# ============================================================
@router.get("/sede/{sede_id}", response_model=list[schemas.TicketOut])
def get_tickets_sede(sede_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Ticket, models.Servicio.nombre.label("servicio_nombre"))
        .join(models.Servicio, models.Ticket.servicio_id == models.Servicio.id)
        .filter(models.Ticket.sede_id == sede_id)
        .order_by(models.Ticket.hora_creacion.asc())
        .all()
    )

    resultado = []
    for ticket, servicio_nombre in rows:
        data = ticket.__dict__.copy()
        data["servicio_nombre"] = servicio_nombre
        resultado.append(data)

    return resultado


# ============================================================
# OBTENER TICKETS POR ESTADO
# ============================================================
@router.get("/sede/{sede_id}/estado/{estado}", response_model=list[schemas.TicketOut])
def get_tickets_estado(sede_id: str, estado: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Ticket, models.Servicio.nombre.label("servicio_nombre"))
        .join(models.Servicio, models.Ticket.servicio_id == models.Servicio.id)
        .filter(
            models.Ticket.sede_id == sede_id,
            models.Ticket.estado == estado,
        )
        .order_by(models.Ticket.hora_creacion.asc())
        .all()
    )

    resultado = []
    for ticket, servicio_nombre in rows:
        data = ticket.__dict__.copy()
        data["servicio_nombre"] = servicio_nombre
        resultado.append(data)

    return resultado


# ============================================================
# LLAMAR TICKET
# ============================================================
@router.put("/llamar/{ticket_id}", response_model=schemas.TicketOut)
def llamar_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    ticket.estado = "llamado"
    ticket.hora_llamado = datetime.now()

    db.commit()
    db.refresh(ticket)

    servicio = db.query(models.Servicio).filter(models.Servicio.id == ticket.servicio_id).first()

    data = ticket.__dict__.copy()
    data["servicio_nombre"] = servicio.nombre

    return data


# ============================================================
# CERRAR TICKET
# ============================================================
@router.put("/cerrar/{ticket_id}", response_model=schemas.TicketOut)
def cerrar_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    ticket.estado = "cerrado"
    ticket.hora_cierre = datetime.now()

    db.commit()
    db.refresh(ticket)

    servicio = db.query(models.Servicio).filter(models.Servicio.id == ticket.servicio_id).first()

    data = ticket.__dict__.copy()
    data["servicio_nombre"] = servicio.nombre

    return data


# ============================================================
# ELIMINAR TICKET
# ============================================================
@router.delete("/eliminar/{ticket_id}")
def eliminar_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    db.delete(ticket)
    db.commit()

    return {"mensaje": "Ticket eliminado correctamente"}


# ============================================================
# WEBSOCKET: SEGUIR TICKET EN TIEMPO REAL
# ============================================================
@router.websocket("/ws/ticket/{ticket_id}")
async def ticket_ws(websocket: WebSocket, ticket_id: str):
    await websocket.accept()
    db = SessionLocal()
    try:
        last_payload = None
        while True:
            ticket = (
                db.query(models.Ticket, models.Servicio.nombre.label("servicio_nombre"))
                .join(models.Servicio, models.Ticket.servicio_id == models.Servicio.id)
                .filter(models.Ticket.id == ticket_id)
                .first()
            )

            if not ticket:
                await websocket.send_json({"error": "Ticket no encontrado"})
                await asyncio.sleep(2)
                continue

            ticket_obj, servicio_nombre = ticket
            data = ticket_obj.__dict__.copy()
            data["servicio_nombre"] = servicio_nombre

            # opcional: si tienes puesto_id y locaciones
            if hasattr(ticket_obj, "puesto_id") and ticket_obj.puesto_id:
                loc = db.query(models.Locacion).filter(models.Locacion.id == ticket_obj.puesto_id).first()
                data["puesto_nombre"] = loc.nombre if loc else "No asignado"
            else:
                data["puesto_nombre"] = "No asignado"

            # solo enviar si cambió
            if data != last_payload:
                await websocket.send_json(data)
                last_payload = data

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    finally:
        db.close()
