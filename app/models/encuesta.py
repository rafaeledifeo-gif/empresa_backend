from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class EncuestaRespuesta(Base):
    __tablename__ = "encuesta_respuestas"

    id          = Column(String,  primary_key=True, index=True)
    ticket_id   = Column(String,  ForeignKey("tickets.id"),   nullable=True)
    servicio_id = Column(String,  ForeignKey("servicios.id"), nullable=True)
    sede_id     = Column(String,  ForeignKey("sedes.id"),     nullable=True)
    cliente_id  = Column(String,  nullable=True)
    tipo        = Column(String,  nullable=True)   # presencial | virtual
    p1_atencion = Column(Integer, nullable=True)   # ¿Cómo calificás la atención?
    p2_video    = Column(Integer, nullable=True)   # ¿Calidad del video y sonido?
    p3_general  = Column(Integer, nullable=True)   # Calificación general
    comentario  = Column(String,  nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
