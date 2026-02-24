from app.database import Base

# ============================================================
# ORDEN IMPORTANTÍSIMO: respetar dependencias entre tablas
# ============================================================

# 1. Sin dependencias
from .empresas import Empresa
from .clientes import Cliente

# 2. Depende de Empresa
from .sedes import Sede

# 3. Depende de Sede
from .servicios import Servicio, funcion_servicio
from .funciones import Funcion
from .locaciones import Locacion
from .usuarios import Usuario
from .calendarios import (
    Calendario,
    CalendarioHorario,
    CalendarioFestivo,
    CalendarioBloqueo,
    CalendarioDisponibilidad,
)

# 4. Depende de Servicio, Sede, Cliente
from .tickets import Ticket

# 5. Depende de todo lo anterior
from .citas import Cita