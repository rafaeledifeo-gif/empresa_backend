# ============================================================
# IMPORTAR SCHEMAS DEL MÓDULO DE CALENDARIOS
# ============================================================

from .calendarios import (
    CalendarioBase,
    CalendarioCreate,
    Calendario,
    CalendarioHorario,
    CalendarioFestivo,
    CalendarioBloqueo,
    CalendarioDisponibilidad,
)

# ============================================================
# IMPORTS COMPARTIDOS
# ============================================================

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# ============================================================
# EMPRESA
# ============================================================

class EmpresaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    direccion: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    id: str

class EmpresaUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    direccion: Optional[str] = None
    cantidad_sedes: Optional[int] = None
    cantidad_usuarios: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class EmpresaOut(EmpresaBase):
    id: str
    cantidad_sedes: int
    cantidad_usuarios: int
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# SEDE
# ============================================================

class SedeBase(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    telefono: Optional[str] = None
    empresa_id: str

class SedeCreate(SedeBase):
    id: str

class SedeOut(SedeBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class SedeUpdate(BaseModel):
    nombre: str
    direccion: str
    ciudad: str
    telefono: str
    empresa_id: str
    ultima_actualizacion: Optional[datetime] = None

# ============================================================
# SERVICIO
# ============================================================

class ServicioBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    sede_id: str
    identificador_letra: str
    rango_inicio: int
    rango_fin: int
    tipo_servicio: Optional[str] = "directo"   # "directo" o "cita"
    calendario_id: Optional[str] = None

class ServicioCreate(ServicioBase):
    id: str

class ServicioUpdate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    identificador_letra: str
    rango_inicio: int
    rango_fin: int
    tipo_servicio: Optional[str] = "directo"
    calendario_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ServicioOut(ServicioBase):
    id: str
    contador_actual: int
    ultima_generacion: Optional[datetime] = None
    activo: bool
    tipo_servicio: str = "directo"
    calendario_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class TurnoResponse(BaseModel):
    turno: str
    numero: int
    letra: str

# ============================================================
# FUNCION
# ============================================================

class FuncionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    sede_id: str
    servicios: List[str] = Field(default_factory=list)

class FuncionCreate(FuncionBase):
    id: str

class FuncionOut(FuncionBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# LOCACION
# ============================================================

class LocacionBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    sede_id: str

class LocacionCreate(LocacionBase):
    id: str

class LocacionOut(LocacionBase):
    id: str
    ultima_actualizacion: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# USUARIO
# ============================================================

class UsuarioBase(BaseModel):
    nombre: str
    apellido: Optional[str] = None
    username: str
    perfil: str
    estado: str
    funcion_id: Optional[str] = None
    empresa_id: Optional[str] = None
    sede_id: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    id: str
    password: str

class UsuarioOut(UsuarioBase):
    id: str
    ultima_actualizacion: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# AUTH
# ============================================================

class LoginData(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

# ============================================================
# CLIENTE
# ============================================================

class ClienteBase(BaseModel):
    nombre: str
    email: str

class ClienteCreate(ClienteBase):
    id: Optional[str] = None
    password: str

class ClienteOut(ClienteBase):
    id: str
    fecha_creacion: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ClienteLogin(BaseModel):
    email: str
    password: str

# ============================================================
# TICKET
# ============================================================

class TicketBase(BaseModel):
    servicio_id: str
    notas: Optional[str] = None
    sede_id: str

class TicketCreate(TicketBase):
    pass

class TicketOut(TicketBase):
    id: str
    codigo: str
    estado: str
    hora_creacion: datetime
    hora_llamado: Optional[datetime] = None
    hora_cierre: Optional[datetime] = None
    servicio_nombre: str
    cliente_id: Optional[str] = None
    cita_id: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# ============================================================
# CITA
# ============================================================

class CitaCreate(BaseModel):
    id: Optional[str] = None
    cliente_id: str
    servicio_id: str
    sede_id: str
    calendario_id: str
    fecha: str
    hora: str
    notas: Optional[str] = None
    qr_token: Optional[str] = None

class CitaOut(BaseModel):
    id: str
    cliente_id: str
    servicio_id: str
    sede_id: str
    calendario_id: str
    fecha: str
    hora: str
    estado: str
    ticket_id: Optional[str] = None
    metodo_checkin: Optional[str] = None
    hora_checkin: Optional[datetime] = None
    cita_original_id: Optional[str] = None
    notas: Optional[str] = None
    qr_token: Optional[str] = None
    created_at: Optional[datetime] = None
    servicio_nombre: Optional[str] = None
    cliente_nombre: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class CitaReagendar(BaseModel):
    nueva_fecha: str
    nueva_hora: str
    calendario_id: str

class CitaCheckin(BaseModel):
    metodo: str
    qr_token: Optional[str] = None