from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.models.calendarios import (
    Calendario,
    CalendarioHorario,
    CalendarioFestivo,
    CalendarioBloqueo,
    CalendarioDisponibilidad,
    CalendarioDiaEspecial,
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


def _parse_time_str(val) -> time | None:
    """Convierte '09:00' o '09:00:00' a time; None si inválido."""
    if not val or not isinstance(val, str):
        return None
    try:
        parts = val.split(":")
        return time(int(parts[0]), int(parts[1]))
    except Exception:
        return None


def _config_dict_a_bloques(cfg: dict) -> list:
    """
    Convierte el dict de config del frontend (manana_activo, tarde_activo, ...)
    a una lista de objetos con los atributos necesarios para generar slots.
    """
    class BloqueSimple:
        def __init__(self, hora_inicio, hora_fin, es_bloque, capacidad_maxima, duracion_cita):
            self.hora_inicio = hora_inicio
            self.hora_fin = hora_fin
            self.es_bloque = es_bloque
            self.capacidad_maxima = capacidad_maxima
            self.duracion_cita = duracion_cita

    bloques = []
    for prefijo in ("manana", "tarde"):
        if not cfg.get(f"{prefijo}_activo"):
            continue
        hi = _parse_time_str(cfg.get(f"{prefijo}_inicio"))
        hf = _parse_time_str(cfg.get(f"{prefijo}_fin"))
        if not hi or not hf:
            continue
        bloques.append(BloqueSimple(
            hora_inicio=hi,
            hora_fin=hf,
            es_bloque=cfg.get(f"{prefijo}_es_bloque", False),
            capacidad_maxima=cfg.get(f"{prefijo}_capacidad_maxima"),
            duracion_cita=cfg.get(f"{prefijo}_duracion_cita"),
        ))
    return bloques


def _slots_de_bloques(bloques: list) -> list:
    """Genera lista de time slots a partir de una lista de BloqueSimple."""
    slots = []
    for b in bloques:
        if not b.hora_inicio or not b.hora_fin:
            continue
        if b.es_bloque:
            capacidad = b.capacidad_maxima or 1
            for _ in range(capacidad):
                slots.append(b.hora_inicio)
        elif b.duracion_cita and b.duracion_cita > 0:
            slots.extend(generar_slots_bloque(b.hora_inicio, b.hora_fin, b.duracion_cita))
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

    # Cargar días con horario especial (override individual de día)
    dias_especiales = {
        d.fecha: d.config
        for d in db.query(CalendarioDiaEspecial).filter(
            CalendarioDiaEspecial.calendario_id == calendario_id,
            CalendarioDiaEspecial.fecha >= fecha_inicio,
            CalendarioDiaEspecial.fecha <= fecha_fin,
        ).all()
    }

    actual = fecha_inicio
    nuevas = []

    while actual <= fecha_fin:
        dia_semana = actual.isoweekday()

        # Días especiales (override manual): tienen su propia config
        if actual in dias_especiales:
            cfg = dias_especiales[actual]
            bloques_esp = _config_dict_a_bloques(cfg)
            if bloques_esp:
                slots = _slots_de_bloques(bloques_esp)
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
            continue

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
            if not b.hora_inicio or not b.hora_fin:
                continue
            if b.es_bloque:
                # Modo "por turnos": crear (capacidad_maxima) slots a la hora de inicio
                # Cada slot representa un cupo; múltiples personas pueden reservar la misma hora
                capacidad = b.capacidad_maxima or 1
                for _ in range(capacidad):
                    slots.append(b.hora_inicio)
            elif b.duracion_cita and b.duracion_cita > 0:
                # Modo "por minutos": slots individuales por duración
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
    """
    Devuelve TODOS los slots del día (disponibles y ocupados) para que el
    frontend pueda mostrar la capacidad real: disponibles / total.
    """
    return db.query(CalendarioDisponibilidad).filter(
        CalendarioDisponibilidad.calendario_id == calendario_id,
        CalendarioDisponibilidad.fecha == fecha,
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