from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Cita(Base):
    __tablename__ = "citas"

    id = Column(String, primary_key=True, index=True)
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=False)
    servicio_id = Column(String, ForeignKey("servicios.id"), nullable=False)
    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)
    calendario_id = Column(String, ForeignKey("calendarios.id"), nullable=False)
    fecha = Column(String, nullable=False)
    hora = Column(String, nullable=False)
    estado = Column(String, nullable=False, default="agendada")
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=True)
    metodo_checkin = Column(String, nullable=True)
    hora_checkin = Column(DateTime, nullable=True)
    cita_original_id = Column(String, ForeignKey("citas.id"), nullable=True)
    notas = Column(String, nullable=True)
    qr_token = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    cliente = relationship("Cliente")
    servicio = relationship("Servicio")
    sede = relationship("Sede")
    ticket = relationship("Ticket", foreign_keys=[ticket_id])
