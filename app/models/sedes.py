from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Sede(Base):
    __tablename__ = "sedes"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    direccion = Column(String)
    ciudad = Column(String)
    telefono = Column(String)
    empresa_id = Column(String, ForeignKey("empresas.id"))
    ultima_actualizacion = Column(DateTime, onupdate=func.now())

    empresa = relationship("Empresa", back_populates="sedes")
    servicios = relationship("Servicio", back_populates="sede", cascade="all, delete")
    funciones = relationship("Funcion", back_populates="sede", cascade="all, delete")
    locaciones = relationship("Locacion", back_populates="sede", cascade="all, delete")
    usuarios = relationship("Usuario", back_populates="sede", cascade="all, delete")
