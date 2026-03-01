from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from typing import Optional
import uuid

from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/reportes", tags=["Reportes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _minutos(d: Optional[timedelta]) -> Optional[float]:
    if d is None:
        return None
    return round(d.total_seconds() / 60, 1)


# ============================================================
# REPORTE NIVEL DE SERVICIO
# ============================================================

@router.get("/nivel-servicio/{sede_id}")
def reporte_nivel_servicio(
    sede_id: str,
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    # Rango de fechas
    if fecha_inicio and fecha_fin:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
    else:
        ff = datetime.now()
        fi = ff - timedelta(days=30)

    # Tickets del rango
    tickets = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.sede_id == sede_id,
            models.Ticket.hora_creacion >= fi,
            models.Ticket.hora_creacion < ff,
        )
        .all()
    )

    # Servicios activos de la sede
    servicios = (
        db.query(models.Servicio)
        .filter(models.Servicio.sede_id == sede_id, models.Servicio.activo == True)
        .all()
    )

    # Metas guardadas
    metas_db = (
        db.query(models.MetaServicioSede)
        .filter(models.MetaServicioSede.sede_id == sede_id)
        .all()
    )
    metas_map = {m.servicio_id: m for m in metas_db}

    # Calcular por servicio
    servicios_data = []
    for svc in servicios:
        ts = [t for t in tickets if t.servicio_id == svc.id]
        atendidos = [t for t in ts if t.estado == "cerrado"]

        esperas = [
            (t.hora_llamado - t.hora_creacion).total_seconds() / 60
            for t in ts if t.hora_llamado and t.hora_creacion
        ]
        atenciones = [
            (t.hora_cierre - t.hora_llamado).total_seconds() / 60
            for t in atendidos if t.hora_cierre and t.hora_llamado
        ]

        prom_espera = round(sum(esperas) / len(esperas), 1) if esperas else None
        prom_atencion = round(sum(atenciones) / len(atenciones), 1) if atenciones else None

        meta = metas_map.get(svc.id)
        meta_espera = meta.meta_espera if meta else 15
        meta_atencion = meta.meta_atencion if meta else 20

        # Cumplimientos
        cumpl_espera = None
        if esperas:
            dentro = sum(1 for e in esperas if e <= meta_espera)
            cumpl_espera = round(dentro / len(esperas) * 100, 1)

        cumpl_atencion = None
        if atenciones:
            dentro = sum(1 for a in atenciones if a <= meta_atencion)
            cumpl_atencion = round(dentro / len(atenciones) * 100, 1)

        # Nivel de servicio (60% espera + 40% atención)
        nivel = None
        if cumpl_espera is not None and cumpl_atencion is not None:
            nivel = round(cumpl_espera * 0.6 + cumpl_atencion * 0.4, 1)
        elif cumpl_espera is not None:
            nivel = cumpl_espera

        servicios_data.append({
            "servicio_id": svc.id,
            "servicio_nombre": svc.nombre,
            "volumen": len(ts),
            "atendidos": len(atendidos),
            "espera_real": prom_espera,
            "meta_espera": meta_espera,
            "desviacion_espera": round(prom_espera - meta_espera, 1) if prom_espera else None,
            "cumplimiento_espera": cumpl_espera,
            "atencion_real": prom_atencion,
            "meta_atencion": meta_atencion,
            "desviacion_atencion": round(prom_atencion - meta_atencion, 1) if prom_atencion else None,
            "cumplimiento_atencion": cumpl_atencion,
            "nivel_servicio": nivel,
        })

    # KPIs globales ponderados por volumen
    total_volumen = sum(s["volumen"] for s in servicios_data)

    def ponderado(campo):
        datos = [(s[campo], s["volumen"]) for s in servicios_data if s[campo] is not None]
        if not datos:
            return None
        total = sum(v for _, v in datos)
        if total == 0:
            return None
        return round(sum(v * v_vol for v, v_vol in datos) / total, 1)

    kpis = {
        "volumen_total": total_volumen,
        "espera_promedio_global": ponderado("espera_real"),
        "atencion_promedio_global": ponderado("atencion_real"),
        "cumplimiento_espera_global": ponderado("cumplimiento_espera"),
        "cumplimiento_atencion_global": ponderado("cumplimiento_atencion"),
        "nivel_servicio_global": ponderado("nivel_servicio"),
    }

    return {
        "fecha_inicio": fi.strftime("%Y-%m-%d"),
        "fecha_fin": (ff - timedelta(days=1)).strftime("%Y-%m-%d"),
        "kpis": kpis,
        "servicios": servicios_data,
    }


# ============================================================
# GUARDAR / ACTUALIZAR METAS
# ============================================================

@router.put("/metas/{sede_id}/{servicio_id}")
def guardar_meta(
    sede_id: str,
    servicio_id: str,
    meta_espera: int = Query(...),
    meta_atencion: int = Query(...),
    db: Session = Depends(get_db),
):
    meta = (
        db.query(models.MetaServicioSede)
        .filter(
            models.MetaServicioSede.sede_id == sede_id,
            models.MetaServicioSede.servicio_id == servicio_id,
        )
        .first()
    )
    if meta:
        meta.meta_espera = meta_espera
        meta.meta_atencion = meta_atencion
        meta.updated_at = datetime.now()
    else:
        meta = models.MetaServicioSede(
            id=str(uuid.uuid4()),
            sede_id=sede_id,
            servicio_id=servicio_id,
            meta_espera=meta_espera,
            meta_atencion=meta_atencion,
        )
        db.add(meta)
    db.commit()
    return {"status": "ok", "meta_espera": meta_espera, "meta_atencion": meta_atencion}


# ============================================================
# REPORTE CITAS PROGRAMADAS (7 días)
# ============================================================

@router.get("/citas-programadas/{sede_id}")
def reporte_citas_programadas(
    sede_id: str,
    db: Session = Depends(get_db),
):
    hoy = date.today()
    hasta = hoy + timedelta(days=7)

    # Citas agendadas en el rango
    citas = (
        db.query(models.Cita, models.Servicio.nombre.label("svc_nombre"))
        .join(models.Servicio, models.Cita.servicio_id == models.Servicio.id)
        .filter(
            models.Cita.sede_id == sede_id,
            models.Cita.fecha >= str(hoy),
            models.Cita.fecha <= str(hasta),
            models.Cita.estado.in_(["agendada", "check_in", "en_espera"]),
        )
        .all()
    )

    # Disponibilidades totales del rango (capacidad)
    from app.models.calendarios import CalendarioDisponibilidad, Calendario
    calendarios = (
        db.query(Calendario)
        .filter(Calendario.sede_id == sede_id, Calendario.activo == True)
        .all()
    )
    cal_ids = [c.id for c in calendarios]

    disponibilidades = []
    if cal_ids:
        disponibilidades = (
            db.query(CalendarioDisponibilidad)
            .filter(
                CalendarioDisponibilidad.calendario_id.in_(cal_ids),
                CalendarioDisponibilidad.fecha >= hoy,
                CalendarioDisponibilidad.fecha <= hasta,
            )
            .all()
        )

    capacidad_total = len(disponibilidades)
    citas_total = len(citas)
    ocupacion_global = round(citas_total / capacidad_total * 100, 1) if capacidad_total > 0 else 0

    # Por día
    dias = {}
    for i in range(8):
        d = hoy + timedelta(days=i)
        fecha_str = str(d)
        citas_dia = [c for c, _ in citas if c.fecha == fecha_str]
        cap_dia = len([d for d in disponibilidades if str(d.fecha) == fecha_str])
        ocup = round(len(citas_dia) / cap_dia * 100, 1) if cap_dia > 0 else 0
        dias[fecha_str] = {
            "fecha": fecha_str,
            "citas": len(citas_dia),
            "capacidad": cap_dia,
            "ocupacion": ocup,
            "riesgo": "rojo" if ocup >= 85 else "amarillo" if ocup >= 70 else "verde",
        }

    # Por servicio
    servicios = (
        db.query(models.Servicio)
        .filter(models.Servicio.sede_id == sede_id, models.Servicio.activo == True)
        .all()
    )

    servicios_data = []
    for svc in servicios:
        citas_svc = [c for c, sn in citas if c.servicio_id == svc.id]
        ocupacion_svc = round(len(citas_svc) / capacidad_total * 100, 1) if capacidad_total > 0 else 0
        carga_diaria = round(len(citas_svc) / 7, 1)
        servicios_data.append({
            "servicio_id": svc.id,
            "servicio_nombre": svc.nombre,
            "citas_programadas": len(citas_svc),
            "capacidad_disponible": capacidad_total,
            "ocupacion": ocupacion_svc,
            "carga_diaria_promedio": carga_diaria,
            "riesgo": "rojo" if ocupacion_svc >= 85 else "amarillo" if ocupacion_svc >= 70 else "verde",
        })

    # Día más saturado
    dia_max = max(dias.values(), key=lambda d: d["ocupacion"]) if dias else None

    # Servicio más demandado
    svc_max = max(servicios_data, key=lambda s: s["citas_programadas"]) if servicios_data else None

    # Métricas históricas (últimos 30 días)
    hace_30 = hoy - timedelta(days=30)
    citas_hist = (
        db.query(models.Cita)
        .filter(
            models.Cita.sede_id == sede_id,
            models.Cita.fecha >= str(hace_30),
            models.Cita.fecha < str(hoy),
        )
        .all()
    )
    total_hist = len(citas_hist)
    canceladas = len([c for c in citas_hist if c.estado == "cancelada"])
    no_show = len([c for c in citas_hist if c.estado == "no_asistio"])
    reprogramadas = len([c for c in citas_hist if c.cita_original_id is not None])

    tiempos_agendamiento = []
    for c in citas_hist:
        if c.created_at:
            try:
                fecha_cita = datetime.strptime(c.fecha, "%Y-%m-%d")
                diff = (fecha_cita - c.created_at.replace(tzinfo=None)).days
                if diff >= 0:
                    tiempos_agendamiento.append(diff)
            except Exception:
                pass

    metricas_historicas = {
        "demanda_promedio_diaria": round(total_hist / 30, 1) if total_hist else 0,
        "tasa_cancelacion": round(canceladas / total_hist * 100, 1) if total_hist else 0,
        "tasa_no_show": round(no_show / total_hist * 100, 1) if total_hist else 0,
        "tasa_reprogramacion": round(reprogramadas / total_hist * 100, 1) if total_hist else 0,
        "dias_promedio_agendamiento": round(sum(tiempos_agendamiento) / len(tiempos_agendamiento), 1) if tiempos_agendamiento else 0,
    }

    # Índice de riesgo global
    if ocupacion_global >= 85:
        riesgo_global = "rojo"
    elif ocupacion_global >= 70:
        riesgo_global = "amarillo"
    else:
        riesgo_global = "verde"

    return {
        "fecha_inicio": str(hoy),
        "fecha_fin": str(hasta),
        "kpis": {
            "citas_total": citas_total,
            "capacidad_total": capacidad_total,
            "ocupacion_global": ocupacion_global,
            "dia_mas_saturado": dia_max,
            "servicio_mas_demandado": svc_max["servicio_nombre"] if svc_max else None,
            "riesgo_global": riesgo_global,
        },
        "por_dia": list(dias.values()),
        "por_servicio": servicios_data,
        "metricas_historicas": metricas_historicas,
    }
