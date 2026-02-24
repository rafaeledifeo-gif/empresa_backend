from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Funcion(Base):
    __tablename__ = "funciones"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)

    sede = relationship("Sede", back_populates="funciones")
    servicios = relationship(
        "Servicio",
        secondary="funcion_servicio",
        back_populates="funciones"
    )
