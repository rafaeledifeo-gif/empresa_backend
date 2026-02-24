from sqlalchemy import Column, String, Integer, Boolean, Date, Time, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base


class Calendario(Base):
    __tablename__ = "calendarios"

    id = Column(String, primary_key=True, index=True)
    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)

    nombre = Column(String, nullable=False)
    pais = Column(String, nullable=False)

    duracion_cita = Column(Integer, nullable=True)

    trabaja_sabado = Column(Boolean, default=True)
    trabaja_domingo = Column(Boolean, default=False)
    mes_inicio = Column(Integer, default=1)
    activo = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())


class CalendarioHorario(Base):
    __tablename__ = "calendario_horarios"

    id = Column(String, primary_key=True)
    calendario_id = Column(String, ForeignKey("calendarios.id"), nullable=False)
    dia_semana = Column(Integer, nullable=False)
    tipo_bloque = Column(String, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    es_bloque = Column(Boolean, default=False)
    capacidad_maxima = Column(Integer, nullable=True)
    duracion_cita = Column(Integer, nullable=True)


class CalendarioFestivo(Base):
    __tablename__ = "calendario_festivos"

    id = Column(String, primary_key=True)
    calendario_id = Column(String, ForeignKey("calendarios.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    nombre = Column(String, nullable=False)
    bloqueado = Column(Boolean, default=True)


class CalendarioBloqueo(Base):
    __tablename__ = "calendario_bloqueos"

    id = Column(String, primary_key=True)
    calendario_id = Column(String, ForeignKey("calendarios.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=True)
    hora_fin = Column(Time, nullable=True)
    motivo = Column(String, nullable=True)


class CalendarioDisponibilidad(Base):
    __tablename__ = "calendario_disponibilidades"

    id = Column(String, primary_key=True)
    calendario_id = Column(String, ForeignKey("calendarios.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    disponible = Column(Boolean, default=True)
