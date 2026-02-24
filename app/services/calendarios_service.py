from datetime import datetime, timedelta, time, date
from sqlalchemy.orm import Session
from app.models.calendarios import (
    Calendario,
    CalendarioHorario,
    CalendarioFestivo,
    CalendarioBloqueo,
    CalendarioDisponibilidad,
)
import uuid

# ============================================================
# CONFIGURACIÓN
# ============================================================

DIAS_A_GENERAR = 14


# ============================================================
# GENERAR RANGO DE FECHAS
# ============================================================

def generar_rango_fechas(fecha_inicio: date, fecha_fin: date):
    dias = []
    actual = fecha_inicio
    while actual <= fecha_fin:
        dias.append(actual)
        actual += timedelta(days=1)
    return dias


# ============================================================
# OBTENER HORARIOS DEL CALENDARIO
# ============================================================

def obtener_horarios(db: Session, calendario_id: str):
    return db.query(CalendarioHorario).filter(
        CalendarioHorario.calendario_id == calendario_id
    ).all()


# ============================================================
# GENERAR SLOTS POR DÍA (USANDO DURACIÓN DEL BLOQUE)
# ============================================================

def generar_slots_por_dia(horarios):
    slots = []

    for h in horarios:
        # Si el bloque no tiene duración, no genera slots
        if not h.duracion_cita:
            continue

        inicio = datetime.combine(date.today(), h.hora_inicio)
        fin = datetime.combine(date.today(), h.hora_fin)

        actual = inicio
        while actual + timedelta(minutes=h.duracion_cita) <= fin:
            slots.append(actual.time())
            actual += timedelta(minutes=h.duracion_cita)

    return slots


# ============================================================
# EXCLUIR FESTIVOS
# ============================================================

def excluir_festivos(db: Session, calendario_id: str, fechas: list[date]):
    festivos = db.query(CalendarioFestivo).filter(
        CalendarioFestivo.calendario_id == calendario_id,
        CalendarioFestivo.bloqueado == True
    ).all()

    fechas_excluidas = {f.fecha for f in festivos}
    return [f for f in fechas if f not in fechas_excluidas]


# ============================================================
# EXCLUIR BLOQUEOS
# ============================================================

def excluir_bloqueos(db: Session, calendario_id: str, fecha: date, slots: list[time]):
    bloqueos = db.query(CalendarioBloqueo).filter(
        CalendarioBloqueo.calendario_id == calendario_id,
        CalendarioBloqueo.fecha == fecha
    ).all()

    for b in bloqueos:
        if b.hora_inicio and b.hora_fin:
            slots = [
                s for s in slots
                if not (b.hora_inicio <= s <= b.hora_fin)
            ]

    return slots


# ============================================================
# GUARDAR DISPONIBILIDADES
# ============================================================

def guardar_disponibilidades(db: Session, calendario_id: str, fecha: date, slots: list[time]):
    for s in slots:
        disp = CalendarioDisponibilidad(
            id=str(uuid.uuid4()),
            calendario_id=calendario_id,
            fecha=fecha,
            hora=s,
            disponible=True
        )
        db.add(disp)

    db.commit()


# ============================================================
# FUNCIÓN PRINCIPAL: GENERAR DISPONIBILIDADES
# ============================================================

def generar_disponibilidades(db: Session, calendario_id: str, fecha_inicio: date, fecha_fin: date):
    calendario = db.query(Calendario).filter(Calendario.id == calendario_id).first()
    if not calendario:
        return {"error": "Calendario no encontrado"}

    # 1) Rango de fechas
    fechas = generar_rango_fechas(fecha_inicio, fecha_fin)

    # 2) Excluir festivos
    fechas = excluir_festivos(db, calendario_id, fechas)

    # 3) Obtener horarios
    horarios = obtener_horarios(db, calendario_id)

    # 4) Generar slots base usando duración del bloque
    slots_base = generar_slots_por_dia(horarios)

    # 5) Procesar cada fecha
    for f in fechas:
        slots = slots_base.copy()

        # Excluir bloqueos
        slots = excluir_bloqueos(db, calendario_id, f, slots)

        # Guardar disponibilidades
        guardar_disponibilidades(db, calendario_id, f, slots)

    return {"status": "ok", "message": "Disponibilidades generadas"}


# ============================================================
# OBTENER DISPONIBILIDADES POR FECHA
# ============================================================

def obtener_disponibilidades_por_fecha(db: Session, calendario_id: str, fecha: date):
    return db.query(CalendarioDisponibilidad).filter(
        CalendarioDisponibilidad.calendario_id == calendario_id,
        CalendarioDisponibilidad.fecha == fecha,
        CalendarioDisponibilidad.disponible == True
    ).order_by(CalendarioDisponibilidad.hora.asc()).all()


# ============================================================
# OBTENER PRIMER HORARIO DISPONIBLE
# ============================================================

def obtener_primer_disponible(db: Session, calendario_id: str):
    disponibilidad = db.query(CalendarioDisponibilidad).filter(
        CalendarioDisponibilidad.calendario_id == calendario_id,
        CalendarioDisponibilidad.disponible == True,
        CalendarioDisponibilidad.fecha >= date.today()
    ).order_by(
        CalendarioDisponibilidad.fecha.asc(),
        CalendarioDisponibilidad.hora.asc()
    ).first()

    if not disponibilidad:
        return None

    return {
        "fecha": disponibilidad.fecha,
        "hora": disponibilidad.hora
    }


# ============================================================
# GENERACIÓN AUTOMÁTICA (14 días)
# ============================================================

def generar_disponibilidades_automaticas(db: Session, calendario_id: str):
    hoy = date.today()
    fecha_fin = hoy + timedelta(days=DIAS_A_GENERAR)

    return generar_disponibilidades(
        db=db,
        calendario_id=calendario_id,
        fecha_inicio=hoy,
        fecha_fin=fecha_fin
    )
