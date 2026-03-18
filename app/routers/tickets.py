from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..database import SessionLocal
from .. import models, schemas
from sqlalchemy import func
import uuid
import asyncio

router = APIRouter(prefix="/tickets", tags=["Tickets"])


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
    ultima_fecha = None
    if servicio.ultima_generacion is not None:
        if isinstance(servicio.ultima_generacion, datetime):
            ultima_fecha = servicio.ultima_generacion.date()
        elif isinstance(servicio.ultima_generacion, str):
            ultima_fecha = datetime.fromisoformat(servicio.ultima_generacion).date()

    if ultima_fecha is None or ultima_fecha != hoy:
        servicio.contador_actual = servicio.rango_inicio
        servicio.ultima_generacion = hoy.isoformat()

    codigo = f"{servicio.identificador_letra}-{servicio.contador_actual}"

    # Generar sala de video si el ticket es virtual
    ticket_id = str(uuid.uuid4())
    tipo = getattr(data, 'tipo', None) or "presencial"
    sala_video_url = None
    if tipo == "virtual":
        sala_video_url = f"https://meet.jit.si/nexto-{ticket_id[:10]}"

    ticket = models.Ticket(
        id=ticket_id,
        codigo=codigo,
        servicio_id=data.servicio_id,
        notas=data.notas,
        estado="pendiente",
        sede_id=data.sede_id,
        cliente_id=getattr(data, 'cliente_id', None),
        tipo=tipo,
        sala_video_url=sala_video_url,
    )

    servicio.contador_actual += 1
    if servicio.contador_actual > servicio.rango_fin:
        servicio.contador_actual = servicio.rango_inicio

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    data_out = ticket.__dict__.copy()
    data_out["servicio_nombre"] = servicio.nombre
    data_out["puesto_nombre"] = ticket.puesto_nombre or ""
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
    # Cargar nombres de clientes
    cliente_ids = list(set(t.cliente_id for t, _ in rows if t.cliente_id))
    clientes_map = {}
    if cliente_ids:
        clientes = db.query(models.Cliente).filter(models.Cliente.id.in_(cliente_ids)).all()
        clientes_map = {c.id: f"{c.nombre} {getattr(c, 'apellido', '') or ''}".strip() for c in clientes}

    resultado = []
    for ticket, servicio_nombre in rows:
        data = ticket.__dict__.copy()
        data["servicio_nombre"] = servicio_nombre
        data["puesto_nombre"] = ticket.puesto_nombre or ""
        data["cliente_nombre"] = clientes_map.get(ticket.cliente_id, "") if ticket.cliente_id else ""
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
        data["puesto_nombre"] = ticket.puesto_nombre or ""
        resultado.append(data)
    return resultado


# ============================================================
# OBTENER TICKET POR ID
# ============================================================
@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    servicio = db.query(models.Servicio).filter(models.Servicio.id == ticket.servicio_id).first()
    return {
        "id": ticket.id,
        "codigo": ticket.codigo,
        "estado": ticket.estado,
        "servicio_id": ticket.servicio_id,
        "sede_id": ticket.sede_id,
        "notas": ticket.notas,
        "hora_creacion": ticket.hora_creacion,
        "hora_llamado": ticket.hora_llamado,
        "hora_cierre": ticket.hora_cierre,
        "cliente_id": ticket.cliente_id,
        "cita_id": ticket.cita_id,
        "puesto_nombre": ticket.puesto_nombre or "",
        "servicio_nombre": servicio.nombre,
    }


# ============================================================
# LLAMAR TICKET
# ============================================================
@router.put("/llamar/{ticket_id}", response_model=schemas.TicketOut)
def llamar_ticket(
    ticket_id: str,
    puesto_nombre: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if not puesto_nombre:
        raise HTTPException(status_code=400, detail="Debe especificar un puesto")

    ticket.estado = "llamado"
    ticket.hora_llamado = datetime.now()
    ticket.puesto_nombre = puesto_nombre

    db.commit()
    db.refresh(ticket)

    servicio = db.query(models.Servicio).filter(models.Servicio.id == ticket.servicio_id).first()
    data = ticket.__dict__.copy()
    data["servicio_nombre"] = servicio.nombre
    data["puesto_nombre"] = ticket.puesto_nombre or ""
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
    data["puesto_nombre"] = ticket.puesto_nombre or ""
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
# ACTUALIZAR NOTAS DE UN TICKET
# ============================================================
@router.put("/{ticket_id}/notas")
def actualizar_notas(
    ticket_id: str,
    notas: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    ticket.notas = notas
    db.commit()
    db.refresh(ticket)
    servicio = db.query(models.Servicio).filter(models.Servicio.id == ticket.servicio_id).first()
    data = ticket.__dict__.copy()
    data["servicio_nombre"] = servicio.nombre if servicio else ""
    data["puesto_nombre"] = ticket.puesto_nombre or ""
    return data


# ============================================================
# TRANSFERIR TICKET A OTRO SERVICIO
# Mantiene el código original. Lo inserta en la posición
# indicada de la cola destino (por defecto posición 3).
# ============================================================
@router.post("/{ticket_id}/transferir")
def transferir_ticket(
    ticket_id: str,
    nuevo_servicio_id: str,
    posicion: int = 3,
    db: Session = Depends(get_db),
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if ticket.estado not in ("pendiente", "llamado"):
        raise HTTPException(status_code=400, detail="Solo se pueden transferir tickets pendientes o llamados")

    nuevo_servicio = db.query(models.Servicio).filter(models.Servicio.id == nuevo_servicio_id).first()
    if not nuevo_servicio:
        raise HTTPException(status_code=404, detail="Servicio destino no encontrado")

    # Obtener cola pendiente del servicio destino (sin incluir el ticket actual)
    tickets_destino = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.servicio_id == nuevo_servicio_id,
            models.Ticket.estado == "pendiente",
            models.Ticket.id != ticket_id,
        )
        .order_by(models.Ticket.hora_creacion.asc())
        .all()
    )

    n = len(tickets_destino)
    target_idx = posicion - 1  # 0-based

    if n == 0:
        nueva_hora = datetime.utcnow()
    elif target_idx >= n:
        nueva_hora = tickets_destino[-1].hora_creacion + timedelta(seconds=1)
    elif target_idx <= 0:
        nueva_hora = tickets_destino[0].hora_creacion - timedelta(seconds=1)
    else:
        antes   = tickets_destino[target_idx - 1].hora_creacion
        despues = tickets_destino[target_idx].hora_creacion
        diff_ms = (despues - antes).total_seconds() * 1000
        if diff_ms > 1:
            nueva_hora = antes + timedelta(milliseconds=diff_ms / 2)
        else:
            nueva_hora = antes + timedelta(milliseconds=1)
            for t in tickets_destino[target_idx:]:
                t.hora_creacion = t.hora_creacion + timedelta(seconds=1)

    ticket.servicio_id   = nuevo_servicio_id
    ticket.sede_id       = nuevo_servicio.sede_id
    ticket.estado        = "pendiente"
    ticket.hora_creacion = nueva_hora
    ticket.puesto_nombre = None
    ticket.hora_llamado  = None

    db.commit()
    db.refresh(ticket)

    data = ticket.__dict__.copy()
    data["servicio_nombre"] = nuevo_servicio.nombre
    data["puesto_nombre"]   = ""
    return data


# ============================================================
# WEBSOCKET: SEGUIR TICKET EN TIEMPO REAL
# ============================================================
@router.websocket("/ws/ticket/{ticket_id}")
async def ticket_ws(websocket: WebSocket, ticket_id: str):
    await websocket.accept()
    db = SessionLocal()
    try:
        last_estado = None
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

            payload = {
                "estado": ticket_obj.estado,
                "codigo": ticket_obj.codigo,
                "puesto_nombre": ticket_obj.puesto_nombre or "",
                "servicio_nombre": servicio_nombre,
            }

            if payload["estado"] != last_estado:
                await websocket.send_json(payload)
                last_estado = payload["estado"]

            if ticket_obj.estado == "cerrado":
                await asyncio.sleep(2)
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
    finally:
        db.close()