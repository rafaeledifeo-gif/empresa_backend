import app.database
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import (
    reportes,
    empresas,
    sedes,
    servicios,
    funciones,
    locaciones,
    usuarios,
    tickets,
    clientes,
    calendarios,
    citas,
    jaas,
)
from app.database import SessionLocal
from sqlalchemy import text

app = FastAPI(debug=True)

# ============================================================
# STARTUP
# ============================================================
@app.on_event("startup")
def on_startup():
    """Auto-migra columnas faltantes en tablas existentes."""
    db = SessionLocal()
    try:
        migrations = [
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS apellido VARCHAR",
            "ALTER TABLE clientes ADD COLUMN IF NOT EXISTS numero_identificacion VARCHAR",
            # Tabla para horarios personalizados por día específico
            """CREATE TABLE IF NOT EXISTS calendario_dias_especiales (
                id VARCHAR PRIMARY KEY,
                calendario_id VARCHAR NOT NULL REFERENCES calendarios(id),
                fecha DATE NOT NULL,
                config JSONB NOT NULL
            )""",
            """CREATE UNIQUE INDEX IF NOT EXISTS uix_cal_dia_esp
               ON calendario_dias_especiales(calendario_id, fecha)""",
        ]
        for sql in migrations:
            try:
                db.execute(text(sql))
            except Exception as e:
                print(f"Migration skipped: {e}")
        db.commit()

        # Sincronizar disponibilidades con citas existentes.
        # Por cada cita activa (agendada/check_in/en_espera), marcar UN slot como ocupado.
        try:
            sync_sql = text("""
                UPDATE calendario_disponibilidades cd
                SET disponible = false
                WHERE cd.id IN (
                    SELECT DISTINCT ON (c.calendario_id, c.fecha, c.hora)
                        cd2.id
                    FROM citas c
                    JOIN calendario_disponibilidades cd2
                        ON cd2.calendario_id = c.calendario_id
                        AND cd2.fecha = c.fecha::date
                        AND cd2.hora = c.hora::time
                        AND cd2.disponible = true
                    WHERE c.estado IN ('agendada', 'check_in', 'en_espera')
                )
            """)
            result = db.execute(sync_sql)
            db.commit()
            print(f">>> Sync disponibilidades: {result.rowcount} slots marcados como ocupados")
        except Exception as e:
            print(f"Sync disponibilidades error: {e}")
            db.rollback()

    except Exception as e:
        print(f"Startup migration error: {e}")
    finally:
        db.close()

# ============================================================
# DEBUG (opcional)
# ============================================================
@app.get("/debug-columns")
def debug_columns():
    db = SessionLocal()
    try:
        q = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'tickets'")
        r = db.execute(q).fetchall()
        return {"columns": [c[0] for c in r]}
    finally:
        db.close()

# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ROUTERS
# ============================================================
app.include_router(empresas.router)
app.include_router(sedes.router)
app.include_router(servicios.router)
app.include_router(funciones.router)
app.include_router(locaciones.router)
app.include_router(usuarios.router)
app.include_router(tickets.router)
app.include_router(clientes.router)
app.include_router(calendarios.router)
app.include_router(citas.router)
app.include_router(reportes.router)
app.include_router(jaas.router)

# ============================================================
# ROOT
# ============================================================
@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Qeuego activo"}