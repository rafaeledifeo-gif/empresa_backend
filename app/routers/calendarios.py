from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import uuid

from app.database import get_db

from app.models.calendarios import (
    Calendario,
    CalendarioHorario,
    CalendarioFestivo,
    CalendarioBloqueo,
    CalendarioDisponibilidad,
)

from app.schemas.calendarios import (
    CalendarioCreate,
    Calendario as CalendarioSchema,
    ConfigurarSemana
)

from app.services.calendarios_service import (
    generar_disponibilidades_automaticas,
    obtener_disponibilidades_por_fecha,
    obtener_primer_disponible,
)

from pydantic import BaseModel

router = APIRouter(prefix="/calendarios", tags=["Calendarios"])


class CalendarioUpdate(BaseModel):
    nombre: Optional[str] = None
    pais: Optional[str] = None
    trabaja_sabado: Optional[bool] = None
    trabaja_domingo: Optional[bool] = None
    mes_inicio: Optional[int] = None
    activo: Optional[bool] = None


# ============================================================
# CREAR CALENDARIO
# ============================================================

@router.post("/", response_model=CalendarioSchema)
def crear_calendario(data: CalendarioCreate, db: Session = Depends(get_db)):
    nuevo = Calendario(
        id=str(uuid.uuid4()),
        sede_id=data.sede_id,
        nombre=data.nombre,
        pais=data.pais,
        trabaja_sabado=data.trabaja_sabado,
        trabaja_domingo=data.trabaja_domingo,
        mes_inicio=data.mes_inicio,
        activo=data.activo
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# ============================================================
# LISTAR CALENDARIOS POR SEDE
# ============================================================

@router.get("/", response_model=list[CalendarioSchema])
def listar_calendarios(sede_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Calendario)
        .filter(Calendario.sede_id == sede_id)
        .order_by(Calendario.created_at.desc())
        .all()
    )


# ============================================================
# OBTENER CALENDARIO POR ID
# ============================================================

@router.get("/{calendario_id}", response_model=CalendarioSchema)
def obtener_calendario(calendario_id: str, db: Session = Depends(get_db)):
    calendario = db.query(Calendario).filter(Calendario.id == calendario_id).first()
    if not calendario:
        raise HTTPException(status_code=404, detail="Calendario no encontrado")
    return calendario


# ============================================================
# ACTUALIZAR CALENDARIO
# ============================================================

@router.put("/{calendario_id}", response_model=CalendarioSchema)
def actualizar_calendario(
    calendario_id: str,
    data: CalendarioUpdate,
    db: Session = Depends(get_db)
):
    calendario = db.query(Calendario).filter(Calendario.id == calendario_id).first()
    if not calendario:
        raise HTTPException(status_code=404, detail="Calendario no encontrado")

    if data.nombre is not None:
        calendario.nombre = data.nombre
    if data.pais is not None:
        calendario.pais = data.pais
    if data.trabaja_sabado is not None:
        calendario.trabaja_sabado = data.trabaja_sabado
    if data.trabaja_domingo is not None:
        calendario.trabaja_domingo = data.trabaja_domingo
    if data.mes_inicio is not None:
        calendario.mes_inicio = data.mes_inicio
    if data.activo is not None:
        calendario.activo = data.activo

    db.commit()
    db.refresh(calendario)
    return calendario


# ============================================================
# ELIMINAR CALENDARIO
# ============================================================

@router.delete("/{calendario_id}")
def eliminar_calendario(calendario_id: str, db: Session = Depends(get_db)):
    calendario = db.query(Calendario).filter(Calendario.id == calendario_id).first()
    if not calendario:
        raise HTTPException(status_code=404, detail="Calendario no encontrado")

    # Borrar datos relacionados primero
    db.query(CalendarioDisponibilidad).filter(
        CalendarioDisponibilidad.calendario_id == calendario_id
    ).delete()

    db.query(CalendarioHorario).filter(
        CalendarioHorario.calendario_id == calendario_id
    ).delete()

    db.query(CalendarioFestivo).filter(
        CalendarioFestivo.calendario_id == calendario_id
    ).delete()

    db.query(CalendarioBloqueo).filter(
        CalendarioBloqueo.calendario_id == calendario_id
    ).delete()

    db.delete(calendario)
    db.commit()

    return {"status": "ok", "message": "Calendario eliminado"}


# ============================================================
# OBTENER CONFIGURACIÓN SEMANAL
# ============================================================

@router.get("/{calendario_id}/configuracion-semanal")
def obtener_configuracion_semanal(calendario_id: str, db: Session = Depends(get_db)):
    horarios = db.query(CalendarioHorario).filter(
        CalendarioHorario.calendario_id == calendario_id
    ).all()

    respuesta = {
        "lunes": [], "martes": [], "miercoles": [], "jueves": [],
        "viernes": [], "sabado": [], "domingo": []
    }

    for h in horarios:
        nombre = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"][h.dia_semana - 1]
        respuesta[nombre].append({
            "id": h.id,
            "dia_semana": h.dia_semana,
            "tipo_bloque": h.tipo_bloque,
            "hora_inicio": h.hora_inicio,
            "hora_fin": h.hora_fin,
            "es_bloque": h.es_bloque,
            "capacidad_maxima": h.capacidad_maxima,
            "duracion_cita": h.duracion_cita
        })

    return respuesta


# ============================================================
# CONFIGURAR SEMANA COMPLETA
# ============================================================

@router.post("/{calendario_id}/configurar-semana")
def configurar_semana(
    calendario_id: str,
    data: ConfigurarSemana,
    db: Session = Depends(get_db)
):
    # 1. Borrar configuración previa
    db.query(CalendarioHorario).filter(
        CalendarioHorario.calendario_id == calendario_id
    ).delete()

    dias = {
        1: data.lunes, 2: data.martes, 3: data.miercoles, 4: data.jueves,
        5: data.viernes, 6: data.sabado, 7: data.domingo
    }

    # 2. Guardar cada día
    for dia_semana, config in dias.items():
        if not config:
            continue

        if config.manana_hora_inicio and config.manana_hora_fin:
            db.add(CalendarioHorario(
                id=str(uuid.uuid4()),
                calendario_id=calendario_id,
                dia_semana=dia_semana,
                tipo_bloque="manana",
                hora_inicio=config.manana_hora_inicio,
                hora_fin=config.manana_hora_fin,
                es_bloque=config.manana_es_bloque,
                capacidad_maxima=config.manana_capacidad_maxima,
                duracion_cita=config.manana_duracion_cita
            ))

        if config.tarde_hora_inicio and config.tarde_hora_fin:
            db.add(CalendarioHorario(
                id=str(uuid.uuid4()),
                calendario_id=calendario_id,
                dia_semana=dia_semana,
                tipo_bloque="tarde",
                hora_inicio=config.tarde_hora_inicio,
                hora_fin=config.tarde_hora_fin,
                es_bloque=config.tarde_es_bloque,
                capacidad_maxima=config.tarde_capacidad_maxima,
                duracion_cita=config.tarde_duracion_cita
            ))

    db.commit()

    # 3. Regenerar disponibilidad
    generar_disponibilidades_automaticas(db, calendario_id)

    return {"status": "ok", "message": "Semana configurada correctamente"}


# ============================================================
# OBTENER DISPONIBILIDADES POR FECHA
# ============================================================

@router.get("/{calendario_id}/disponibilidades", response_model=list[dict])
def obtener_disponibilidades_endpoint(
    calendario_id: str,
    fecha: date,
    db: Session = Depends(get_db)
):
    disponibilidades = obtener_disponibilidades_por_fecha(
        db=db,
        calendario_id=calendario_id,
        fecha=fecha
    )

    return [
        {
            "id": d.id,
            "fecha": d.fecha,
            "hora": d.hora,
            "disponible": d.disponible
        }
        for d in disponibilidades
    ]


# ============================================================
# PRIMER HORARIO DISPONIBLE
# ============================================================

@router.get("/{calendario_id}/primer-disponible", response_model=dict)
def obtener_primer_disponible_endpoint(
    calendario_id: str,
    db: Session = Depends(get_db)
):
    resultado = obtener_primer_disponible(db=db, calendario_id=calendario_id)

    if not resultado:
        return {"status": "sin_disponibilidad"}

    return {
        "status": "ok",
        "fecha": resultado["fecha"],
        "hora": resultado["hora"]
    }