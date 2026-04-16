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
    encuesta,
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
            # Tabla encuestas de satisfacción
            """CREATE TABLE IF NOT EXISTS encuesta_respuestas (
                id          VARCHAR PRIMARY KEY,
                ticket_id   VARCHAR REFERENCES tickets(id),
                servicio_id VARCHAR REFERENCES servicios(id),
                sede_id     VARCHAR REFERENCES sedes(id),
                cliente_id  VARCHAR,
                tipo        VARCHAR,
                p1_atencion INTEGER,
                p2_video    INTEGER,
                p3_general  INTEGER,
                comentario  VARCHAR,
                created_at  TIMESTAMP DEFAULT NOW()
            )""",
        ]
        for sql in migrations:
            try:
                db.execute(text(sql))
            except Exception as e:
                print(f"Migration skipped: {e}")
        db.commit()

        # Sincronizar disponibilidades con citas existentes.
        # 1) Resetear todos los slots futuros a disponible=True.
        # 2) Por cada cita activa, marcar exactamente UN slot como ocupado,
        #    usando ROW_NUMBER para que 2 citas a las 08:00 marquen 2 slots distintos.
        try:
            # Paso 1: reset
            db.execute(text(
                "UPDATE calendario_disponibilidades SET disponible = true "
                "WHERE fecha >= CURRENT_DATE"
            ))
            db.commit()

            # Paso 2: marcar N slots por cada grupo (calendario_id, fecha, hora)
            sync_sql = text("""
                WITH citas_numeradas AS (
                    SELECT
                        calendario_id,
                        fecha::date  AS fecha,
                        hora::time   AS hora,
                        ROW_NUMBER() OVER (
                            PARTITION BY calendario_id, fecha, hora
                            ORDER BY created_at
                        ) AS n
                    FROM citas
                    WHERE estado IN ('agendada', 'check_in', 'en_espera')
                      AND fecha::date >= CURRENT_DATE
                ),
                slots_numerados AS (
                    SELECT
                        id,
                        calendario_id,
                        fecha,
                        hora,
                        ROW_NUMBER() OVER (
                            PARTITION BY calendario_id, fecha, hora
                            ORDER BY id
                        ) AS n
                    FROM calendario_disponibilidades
                    WHERE fecha >= CURRENT_DATE
                )
                UPDATE calendario_disponibilidades
                SET disponible = false
                WHERE id IN (
                    SELECT sn.id
                    FROM citas_numeradas  cn
                    JOIN slots_numerados  sn
                        ON  sn.calendario_id = cn.calendario_id
                        AND sn.fecha         = cn.fecha
                        AND sn.hora          = cn.hora
                        AND sn.n             = cn.n
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
# ADMIN — resincronizar disponibilidades manualmente
# ============================================================
@app.post("/admin/sync-disponibilidades")
def sync_disponibilidades_manual():
    """
    Resetea todos los slots futuros a disponible=True y luego marca
    exactamente los slots que corresponden a citas activas.
    Útil para corregir estados inconsistentes sin reiniciar el servidor.
    """
    db = SessionLocal()
    try:
        db.execute(text(
            "UPDATE calendario_disponibilidades SET disponible = true "
            "WHERE fecha >= CURRENT_DATE"
        ))
        db.commit()

        result = db.execute(text("""
            WITH citas_numeradas AS (
                SELECT
                    calendario_id,
                    fecha::date  AS fecha,
                    hora::time   AS hora,
                    ROW_NUMBER() OVER (
                        PARTITION BY calendario_id, fecha, hora
                        ORDER BY created_at
                    ) AS n
                FROM citas
                WHERE estado IN ('agendada', 'check_in', 'en_espera')
                  AND fecha::date >= CURRENT_DATE
            ),
            slots_numerados AS (
                SELECT
                    id, calendario_id, fecha, hora,
                    ROW_NUMBER() OVER (
                        PARTITION BY calendario_id, fecha, hora
                        ORDER BY id
                    ) AS n
                FROM calendario_disponibilidades
                WHERE fecha >= CURRENT_DATE
            )
            UPDATE calendario_disponibilidades
            SET disponible = false
            WHERE id IN (
                SELECT sn.id
                FROM citas_numeradas cn
                JOIN slots_numerados sn
                    ON  sn.calendario_id = cn.calendario_id
                    AND sn.fecha         = cn.fecha
                    AND sn.hora          = cn.hora
                    AND sn.n             = cn.n
            )
        """))
        db.commit()
        return {"status": "ok", "slots_ocupados": result.rowcount}
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}
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
app.include_router(encuesta.router)

# ============================================================
# ROOT
# ============================================================
@app.get("/")
def root():
    return {"status": "ok", "message": "Backend Qeuego activo"}