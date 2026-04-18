"""
Router: /stats
Contadores de uso por sede y tipo de app (consola, kiosco, pantalla).
"""
from fastapi import APIRouter
from sqlalchemy import text
from app.database import SessionLocal

router = APIRouter(prefix="/stats", tags=["stats"])


@router.post("/{sede_id}/{app_type}")
def incrementar_contador(sede_id: str, app_type: str):
    """
    Incrementa el contador de uso para una sede y tipo de app.
    app_type: 'consola' | 'kiosco' | 'pantalla'
    """
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO app_stats (sede_id, app_type, contador)
            VALUES (:sede_id, :app_type, 1)
            ON CONFLICT (sede_id, app_type)
            DO UPDATE SET contador = app_stats.contador + 1,
                          updated_at = NOW()
        """), {"sede_id": sede_id, "app_type": app_type})
        db.commit()

        row = db.execute(text("""
            SELECT contador FROM app_stats
            WHERE sede_id = :sede_id AND app_type = :app_type
        """), {"sede_id": sede_id, "app_type": app_type}).fetchone()

        return {"sede_id": sede_id, "app_type": app_type, "contador": row[0] if row else 1}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@router.get("/{sede_id}")
def obtener_contadores(sede_id: str):
    """
    Devuelve todos los contadores de una sede.
    { "consola": 12, "kiosco": 4, "pantalla": 7 }
    """
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT app_type, contador FROM app_stats
            WHERE sede_id = :sede_id
        """), {"sede_id": sede_id}).fetchall()

        result = {"consola": 0, "kiosco": 0, "pantalla": 0}
        for row in rows:
            result[row[0]] = row[1]
        return result
    except Exception as e:
        return {"consola": 0, "kiosco": 0, "pantalla": 0}
    finally:
        db.close()
