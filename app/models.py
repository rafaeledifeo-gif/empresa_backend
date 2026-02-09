from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy import Table

# ============================================================
# TABLA INTERMEDIA MANY-TO-MANY
# ============================================================

funcion_servicio = Table(
    "funcion_servicio",
    Base.metadata,
    Column("funcion_id", String, ForeignKey("funciones.id"), primary_key=True),
    Column("servicio_id", String, ForeignKey("servicios.id"), primary_key=True)
)

# ============================================================
# EMPRESA
# ============================================================

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

# ============================================================
# SEDE
# ============================================================

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

# ============================================================
# SERVICIO
# ============================================================

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
    sede = relationship("Sede", back_populates="servicios")

    # 🔥 NUEVO CAMPO PARA ACTIVAR/DESACTIVAR SERVICIOS
    activo = Column(Boolean, default=True)

    # 🔥 RELACIÓN MANY‑TO‑MANY
    funciones = relationship(
        "Funcion",
        secondary="funcion_servicio",
        back_populates="servicios"
    )

# ============================================================
# FUNCION
# ============================================================

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

# ============================================================
# LOCACION
# ============================================================

class Locacion(Base):
    __tablename__ = "locaciones"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)

    ultima_actualizacion = Column(DateTime, onupdate=func.now())

    sede = relationship("Sede", back_populates="locaciones")

# ============================================================
# USUARIO
# ============================================================

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=True)

    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    perfil = Column(String, nullable=False)   # admin, operador, supervisor
    estado = Column(String, nullable=False)   # activo / inactivo

    funcion_id = Column(String, ForeignKey("funciones.id"), nullable=True)

    empresa_id = Column(String, ForeignKey("empresas.id"))
    sede_id = Column(String, ForeignKey("sedes.id"))

    ultima_actualizacion = Column(DateTime, onupdate=func.now())

    sede = relationship("Sede", back_populates="usuarios")
    funcion = relationship("Funcion")

# ============================================================
# TICKET
# ============================================================
# force rebuild
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)
    codigo = Column(String, nullable=False)
    servicio_id = Column(String, ForeignKey("servicios.id"), nullable=False)
    servicio = relationship("Servicio")

    notas = Column(String)

    estado = Column(String, default="pendiente")  # pendiente, llamado, cerrado

    hora_creacion = Column(DateTime, server_default=func.now())
    hora_llamado = Column(DateTime, nullable=True)
    hora_cierre = Column(DateTime, nullable=True)

    sede_id = Column(String, ForeignKey("sedes.id"), nullable=False)
    sede = relationship("Sede")

    puesto_nombre = Column(String, nullable=True)
# ============================================================
# CLIENTE (para app móvil)
# ============================================================

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)

    fecha_creacion = Column(DateTime, server_default=func.now())
