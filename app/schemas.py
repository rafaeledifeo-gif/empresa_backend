
from typing import Optional, List
from datetime import datetime
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
    activo: bool  # ✅ CAMPO NUEVO PARA ACTIVAR/DESACTIVAR

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
    servicios: List[str] = Field(default_factory=list) # ✔ seguro y correcto

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
    servicio_nombre: str # ← AGREGADO 
    
    model_config = ConfigDict(from_attributes=True)