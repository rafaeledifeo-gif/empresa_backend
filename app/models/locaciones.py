from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Locacion(Base):
    __tablename__ = "locaciones"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)
    ultima_actualizacion = Column(DateTime, onupdate=func.now())

    sede = relationship("Sede", back_populates="locaciones")
