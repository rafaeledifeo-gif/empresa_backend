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

from app.database import db
from sqlalchemy import text

app = FastAPI(debug=True)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/debug-columns")
def debug_columns():
    q = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tickets'")
    r = db.session.execute(q).fetchall()
    return {"columns": [c[0] for c in r]}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return {}

app.include_router(empresas.router)
app.include_router(sedes.router)
app.include_router(servicios.router)
app.include_router(funciones.router)
app.include_router(locaciones.router)
app.include_router(usuarios.router)
app.include_router(tickets.router)
app.include_router(clientes.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Qeuego activo"}
