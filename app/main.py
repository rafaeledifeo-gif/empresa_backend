import app.database
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .init_db import init_db
from .routers import (
    empresas,
    sedes,
    servicios,
    funciones,
    locaciones,
    usuarios,
    tickets,
    clientes,
)

app = FastAPI(debug=True)

@app.on_event("startup")
def on_startup():
    init_db()

# ⭐ CORS CORREGIDO PARA FLUTTER WEB
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # permite cualquier origen
    allow_origin_regex=".*",      # permite puertos dinámicos (Flutter Web)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⭐ RUTA OPTIONS PARA PREFLIGHT (NECESARIA EN NAVEGADOR)
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return {}

# Routers
app.include_router(empresas.router)
app.include_router(sedes.router)
app.include_router(servicios.router)
app.include_router(funciones.router)
app.include_router(locaciones.router)
app.include_router(usuarios.router)
app.include_router(tickets.router)
app.include_router(clientes.router)

# Ruta raíz
@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Qeuego activo"}
