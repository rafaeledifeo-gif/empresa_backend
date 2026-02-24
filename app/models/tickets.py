from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)
    codigo = Column(String, nullable=False)
    servicio_id = Column(String, ForeignKey("servicios.id"), nullable=False)
    notas = Column(String)
    estado = Column(String, default="pendiente")
    hora_creacion = Column(DateTime, server_default=func.now())
    hora_llamado = Column(DateTime, nullable=True)
    hora_cierre = Column(DateTime, nullable=True)
    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)
    puesto_nombre = Column(String, nullable=True)
    cliente_id = Column(String, ForeignKey("clientes.id"), nullable=True)
    cita_id = Column(String, ForeignKey("citas.id"), nullable=True)

    servicio = relationship("Servicio")
    sede = relationship("Sede")
    cliente = relationship("Cliente")
