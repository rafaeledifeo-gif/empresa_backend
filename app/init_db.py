from .database import Base, engine
from .models import Empresa, Sede, Servicio, Funcion, Locacion, Usuario, Ticket, Cliente

def init_db():
    Base.metadata.create_all(bind=engine)
