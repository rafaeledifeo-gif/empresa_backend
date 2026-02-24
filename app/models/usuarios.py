from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    perfil = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    funcion_id = Column(String, ForeignKey("funciones.id"), nullable=True)
    empresa_id = Column(String, ForeignKey("empresas.id"))
    sede_id = Column(String, ForeignKey("sedes.id"))
    ultima_actualizacion = Column(DateTime, onupdate=func.now())

    sede = relationship("Sede", back_populates="usuarios")
    funcion = relationship("Funcion")
