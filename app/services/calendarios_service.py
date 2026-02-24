from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.models.calendarios import (
    Calendario,
    CalendarioHorario,
    CalendarioFestivo,
    CalendarioBloqueo,
    CalendarioDisponibilidad,
)
import uuid

def generar_rango_fechas(fecha_inicio: date, fecha_fin: date):
    dias = []
    actual = fecha_inicio
    while actual <= fecha_fin:
        dias.append(actual)
        actual += timedelta(days=1)
    return dias


def obtener_horarios(db: Session, calendario_id: str):
    return db.query(CalendarioHorario).filter(
        CalendarioHorario.calendario_id == calendario_id
    ).all()


def generar_slots_bloque(hora_inicio: time, hora_fin: time, duracion: int):
    slots = []
    base = date.today()
    actual = datetime.combine(base, hora_inicio)
    fin = datetime.combine(base, hora_fin)
    while actual + timedelta(minutes=duracion) <= fin:
        slots.append(actual.time())
        actual += timedelta(minutes=duracion)
    return slots


def excluir_festivos(db: Session, calendario_id: str, fechas: list):
    festivos = db.query(CalendarioFestivo).filter(
        CalendarioFestivo.calendario_id == calendario_id,
        CalendarioFestivo.bloqueado == True
    ).all()
    fechas_excluidas = {f.fecha for f in festivos}
    return [f for f in fechas if f not in fechas_excluidas]


def excluir_bloqueos(db: Session, calendario_id: str, fecha: date, slots: list):
    bloqueos = db.query(CalendarioBloqueo).filter(
        CalendarioBloqueo.calendario_id == calendario_id,
        CalendarioBloqueo.fecha == fecha
    ).all()
    for b in bloqueos:
        if b.hora_inicio and b.hora_fin:
            slots = [s for s in slots if not (b.hora_inicio <= s <= b.hora_fin)]
    return slots


def generar_disponibilidades(
    db: Session,
    calendario_id: str,
    fecha_inicio: date,
    fecha_fin: date
):
    calendario = db.query(Calendario).filter(Calendario.id == calendario_id).first()
    if not calendario:
        return {"error": "Calendario no encontrado"}

    horarios = obtener_horarios(db, calendario_id)
    print(f">>> horarios encontrados: {len(horarios)}")

    horarios_por_dia = {}
    for h in horarios:
        horarios_por_dia.setdefault(h.dia_semana, []).append(h)

    festivos = {
        f.fecha for f in db.query(CalendarioFestivo).filter(
            CalendarioFestivo.calendario_id == calendario_id,
            CalendarioFestivo.bloqueado == True
        ).all()
    }

    actual = fecha_inicio
    nuevas = []

    while actual <= fecha_fin:
        dia_semana = actual.isoweekday()

        if dia_semana == 6 and not calendario.trabaja_sabado:
            actual += timedelta(days=1)
            continue
        if dia_semana == 7 and not calendario.trabaja_domingo:
            actual += timedelta(days=1)
            continue

        if actual in festivos:
            actual += timedelta(days=1)
            continue

        bloques = horarios_por_dia.get(dia_semana, [])
        if not bloques:
            actual += timedelta(days=1)
            continue

        slots = []
        for b in bloques:
            if b.duracion_cita and b.hora_inicio and b.hora_fin:
                slots.extend(
                    generar_slots_bloque(b.hora_inicio, b.hora_fin, b.duracion_cita)
                )

        slots = excluir_bloqueos(db, calendario_id, actual, slots)

        for s in slots:
            nuevas.append(CalendarioDisponibilidad(
                id=str(uuid.uuid4()),
                calendario_id=calendario_id,
                fecha=actual,
                hora=s,
                disponible=True
            ))

        actual += timedelta(days=1)

    print(f">>> slots generados: {len(nuevas)}")

    if nuevas:
        db.bulk_save_objects(nuevas)
        db.commit()

    return {"status": "ok", "generadas": len(nuevas)}


def obtener_disponibilidades_por_fecha(db: Session, calendario_id: str, fecha: date):
    return db.query(CalendarioDisponibilidad).filter(
        CalendarioDisponibilidad.calendario_id == calendario_id,
        CalendarioDisponibilidad.fecha == fecha,
        CalendarioDisponibilidad.disponible == True
    ).order_by(CalendarioDisponibilidad.hora.asc()).all()


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

    return {"fecha": disponibilidad.fecha, "hora": disponibilidad.hora}


def generar_disponibilidades_automaticas(db: Session, calendario_id: str):
    print(f">>> GENERANDO DISPONIBILIDADES para {calendario_id}")

    calendario = db.query(Calendario).filter(Calendario.id == calendario_id).first()
    if not calendario:
        print(">>> CALENDARIO NO ENCONTRADO")
        return

    hoy = date.today()
    fecha_inicio = hoy
    fecha_fin = hoy + relativedelta(months=12)

    print(f">>> rango: {fecha_inicio} → {fecha_fin}")

    # Borrar disponibilidades previas
    db.query(CalendarioDisponibilidad).filter(
        CalendarioDisponibilidad.calendario_id == calendario_id
    ).delete()
    db.commit()

    return generar_disponibilidades(
        db=db,
        calendario_id=calendario_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )