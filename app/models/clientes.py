from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    numero_identificacion = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())