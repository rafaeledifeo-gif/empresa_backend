from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


funcion_servicio = Table(
    "funcion_servicio",
    Base.metadata,
    Column("funcion_id", String, ForeignKey("funciones.id"), primary_key=True),
    Column("servicio_id", String, ForeignKey("servicios.id"), primary_key=True)
)


class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    identificador_letra = Column(String, nullable=False)
    rango_inicio = Column(Integer, nullable=False)
    rango_fin = Column(Integer, nullable=False)
    contador_actual = Column(Integer, nullable=False)
    ultima_generacion = Column(DateTime, server_default=func.now())
    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)
    activo = Column(Boolean, default=True)

    sede = relationship("Sede", back_populates="servicios")
    funciones = relationship(
        "Funcion",
        secondary="funcion_servicio",
        back_populates="servicios"
    )
