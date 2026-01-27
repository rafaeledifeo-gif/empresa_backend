from fastapi import FastAPI
from .init_db import init_db
from .routers import (
    empresas,
    sedes,
    servicios,
    funciones,
    locaciones,
    usuarios,
    tickets,
    clientes,   # 👈 AÑADIDO
)
from fastapi.middleware.cors import CORSMiddleware

init_db()

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes restringirlo luego
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(empresas.router)
app.include_router(sedes.router)
app.include_router(servicios.router)
app.include_router(funciones.router)
app.include_router(locaciones.router)
app.include_router(usuarios.router)
app.include_router(tickets.router)
app.include_router(clientes.router)  # 👈 AÑADIDO
