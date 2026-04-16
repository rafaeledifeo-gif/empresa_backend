import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.database import SessionLocal
from app.models.encuesta import EncuestaRespuesta

router = APIRouter(prefix="/encuesta", tags=["encuesta"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ────────────────────────────────────────────────────
class RespuestaIn(BaseModel):
    ticket_id:   Optional[str] = None
    servicio_id: Optional[str] = None
    sede_id:     Optional[str] = None
    cliente_id:  Optional[str] = None
    tipo:        Optional[str] = None   # presencial | virtual
    p1_atencion: Optional[int] = None
    p2_video:    Optional[int] = None
    p3_general:  Optional[int] = None
    comentario:  Optional[str] = None


# ── POST: guardar respuesta ────────────────────────────────────
@router.post("/respuesta", status_code=201)
def crear_respuesta(data: RespuestaIn, db: Session = Depends(get_db)):
    resp = EncuestaRespuesta(
        id          = str(uuid.uuid4()),
        ticket_id   = data.ticket_id,
        servicio_id = data.servicio_id,
        sede_id     = data.sede_id,
        cliente_id  = data.cliente_id,
        tipo        = data.tipo,
        p1_atencion = data.p1_atencion,
        p2_video    = data.p2_video,
        p3_general  = data.p3_general,
        comentario  = data.comentario,
    )
    db.add(resp)
    db.commit()
    db.refresh(resp)
    return {"id": resp.id, "status": "ok"}


# ── GET: reporte global o por sede ────────────────────────────
@router.get("/reporte")
def reporte(
    sede_id:     Optional[str] = Query(None),
    servicio_id: Optional[str] = Query(None),
    tipo:        Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    filters = []
    params: dict = {}
    if sede_id:
        filters.append("sede_id = :sede_id")
        params["sede_id"] = sede_id
    if servicio_id:
        filters.append("servicio_id = :servicio_id")
        params["servicio_id"] = servicio_id
    if tipo:
        filters.append("tipo = :tipo")
        params["tipo"] = tipo

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    # Promedios globales
    agg = db.execute(text(f"""
        SELECT
            COUNT(*)                       AS total,
            ROUND(AVG(p1_atencion), 2)     AS avg_atencion,
            ROUND(AVG(p2_video),    2)     AS avg_video,
            ROUND(AVG(p3_general),  2)     AS avg_general
        FROM encuesta_respuestas
        {where}
    """), params).mappings().fetchone()

    # Últimos comentarios (máx 50)
    comentarios = db.execute(text(f"""
        SELECT
            er.comentario,
            er.tipo,
            er.created_at,
            s.nombre AS servicio_nombre
        FROM encuesta_respuestas er
        LEFT JOIN servicios s ON s.id = er.servicio_id
        {where}
        {"AND" if where else "WHERE"} er.comentario IS NOT NULL
        AND TRIM(er.comentario) <> ''
        ORDER BY er.created_at DESC
        LIMIT 50
    """), params).mappings().fetchall()

    # Promedios por servicio
    por_servicio = db.execute(text(f"""
        SELECT
            s.nombre                       AS servicio,
            COUNT(er.id)                   AS total,
            ROUND(AVG(er.p1_atencion), 2)  AS avg_atencion,
            ROUND(AVG(er.p2_video),    2)  AS avg_video,
            ROUND(AVG(er.p3_general),  2)  AS avg_general
        FROM encuesta_respuestas er
        LEFT JOIN servicios s ON s.id = er.servicio_id
        {where}
        GROUP BY s.nombre
        ORDER BY total DESC
    """), params).mappings().fetchall()

    return {
        "totales": dict(agg) if agg else {},
        "comentarios": [dict(r) for r in comentarios],
        "por_servicio": [dict(r) for r in por_servicio],
    }
