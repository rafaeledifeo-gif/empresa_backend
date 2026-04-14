from typing import Optional, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field 
from pydantic import ConfigDict

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

class ServicioCreate(ServicioBase):
    id: str

class ServicioOut(ServicioBase):
    id: str
    contador_actual: int
    ultima_generacion: Optional[datetime] = None
    activo: bool

    model_config = ConfigDict(from_attributes=True)

# ============================================================
# RESPUESTA DEL TURNO GENERADO
# ============================================================

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
    cliente_nombre: Optional[str] = None
    cita_id: Optional[str] = None
    puesto_nombre: Optional[str] = None
    tipo: Optional[str] = "presencial"
    sala_video_url: Optional[str] = None

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
    fecha: str        # "2026-03-15"
    hora: str         # "10:30"
    notas: Optional[str] = None
    qr_token: Optional[str] = None

class CitaOut(BaseModel):
    id: str
    cliente_id: str
    servicio_id: str
    sede_id: str
    calendario_id: str
    fecha: date | str
    hora: time | str
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

    from pydantic import field_serializer

    @field_serializer("fecha")
    def serialize_fecha(self, v) -> str:
        return str(v) if v else v

    @field_serializer("hora")
    def serialize_hora(self, v) -> str:
        if v is None:
            return v
        s = str(v)
        return s[:5]  # HH:MM


class CitaReagendar(BaseModel):
    nueva_fecha: str
    nueva_hora: str
    calendario_id: str

class CitaCheckin(BaseModel):
    metodo: str   # 'app' | 'qr'
    qr_token: Optional[str] = None