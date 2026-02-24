from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    direccion = Column(String)
    cantidad_sedes = Column(Integer, default=0)
    cantidad_usuarios = Column(Integer, default=0)
    fecha_creacion = Column(DateTime, server_default=func.now())
    ultima_actualizacion = Column(DateTime, onupdate=func.now())

    sedes = relationship("Sede", back_populates="empresa", cascade="all, delete")
