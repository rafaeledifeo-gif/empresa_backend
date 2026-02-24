from pydantic import BaseModel
from typing import Optional
from datetime import date, time


# ============================================================
# BASE DEL CALENDARIO
# ============================================================

class CalendarioBase(BaseModel):
    nombre: str
    pais: str


# ============================================================
# CREAR CALENDARIO
# ============================================================

class CalendarioCreate(CalendarioBase):
    sede_id: str
    trabaja_sabado: bool
    trabaja_domingo: bool
    mes_inicio: int
    activo: bool


# ============================================================
# CONFIGURACIÓN SEMANAL
# ============================================================

class ConfigurarDia(BaseModel):
    manana_hora_inicio: Optional[time] = None
    manana_hora_fin: Optional[time] = None
    manana_es_bloque: Optional[bool] = None
    manana_capacidad_maxima: Optional[int] = None
    manana_duracion_cita: Optional[int] = None

    tarde_hora_inicio: Optional[time] = None
    tarde_hora_fin: Optional[time] = None
    tarde_es_bloque: Optional[bool] = None
    tarde_capacidad_maxima: Optional[int] = None
    tarde_duracion_cita: Optional[int] = None


class ConfigurarSemana(BaseModel):
    lunes: Optional[ConfigurarDia] = None
    martes: Optional[ConfigurarDia] = None
    miercoles: Optional[ConfigurarDia] = None
    jueves: Optional[ConfigurarDia] = None
    viernes: Optional[ConfigurarDia] = None
    sabado: Optional[ConfigurarDia] = None
    domingo: Optional[ConfigurarDia] = None


# ============================================================
# MODELOS DE RESPUESTA
# ============================================================

class CalendarioHorario(BaseModel):
    id: str
    dia_semana: int
    tipo_bloque: str
    hora_inicio: time
    hora_fin: time
    es_bloque: bool
    capacidad_maxima: Optional[int]
    duracion_cita: Optional[int]

    class Config:
        from_attributes = True


class CalendarioFestivo(BaseModel):
    id: str
    fecha: date
    nombre: str
    bloqueado: bool

    class Config:
        from_attributes = True


class CalendarioBloqueo(BaseModel):
    id: str
    fecha: date
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    motivo: Optional[str]

    class Config:
        from_attributes = True


class CalendarioDisponibilidad(BaseModel):
    id: str
    fecha: date
    hora: time
    disponible: bool

    class Config:
        from_attributes = True


class Calendario(BaseModel):
    id: str
    sede_id: str
    nombre: str
    pais: str
    trabaja_sabado: bool
    trabaja_domingo: bool
    mes_inicio: int
    activo: bool

    class Config:
        from_attributes = True
