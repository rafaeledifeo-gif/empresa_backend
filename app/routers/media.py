"""
media.py — Módulo de distribución de contenido a pantallas TV
Endpoints:
  POST   /media/pantallas            — Registrar pantalla nueva
  GET    /media/pantallas            — Listar pantallas (admin)
  GET    /media/pantallas/{token}    — Info de pantalla por token
  DELETE /media/pantallas/{id}       — Eliminar pantalla

  POST   /media/contenido            — Subir contenido (multipart)
  GET    /media/contenido            — Listar contenido (filtra por sede/empresa)
  DELETE /media/contenido/{id}       — Eliminar contenido

  GET    /media/playlist/{sede_id}   — Playlist activa para una sede
  GET    /media/files/{filename}     — Servir archivo estático

  POST   /media/heartbeat/{token}    — Pantalla informa que está viva
"""

import os
import uuid
import secrets
import shutil
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from .. import models

router = APIRouter(prefix="/media", tags=["Media"])

CORS_HEADERS = {"Access-Control-Allow-Origin": "*"}

# ── Directorio donde se guardan los archivos ────────────────────────────────
MEDIA_DIR = os.environ.get("MEDIA_DIR", "/var/www/media")
os.makedirs(MEDIA_DIR, exist_ok=True)


# ============================================================
# SCHEMAS
# ============================================================

class PantallaCreate(BaseModel):
    nombre: str
    sede_id: Optional[str] = None
    empresa_id: Optional[str] = None
    intervalo_segundos: int = 8

class PantallaOut(BaseModel):
    id: str
    nombre: str
    sede_id: Optional[str]
    empresa_id: Optional[str]
    token: str
    intervalo_segundos: int
    activo: bool
    ultima_conexion: Optional[datetime]
    class Config:
        from_attributes = True

class ContenidoOut(BaseModel):
    id: str
    nombre: str
    tipo: str
    empresa_id: Optional[str]
    sede_id: Optional[str]
    archivo_url: str
    orden: int
    activo: bool
    class Config:
        from_attributes = True


def pantalla_json(p):
    return {
        "id": p.id,
        "nombre": p.nombre,
        "sede_id": p.sede_id,
        "empresa_id": p.empresa_id,
        "token": p.token,
        "intervalo_segundos": p.intervalo_segundos,
        "activo": p.activo,
        "ultima_conexion": p.ultima_conexion.isoformat() if p.ultima_conexion else None,
    }

def contenido_json(c):
    return {
        "id": c.id,
        "nombre": c.nombre,
        "tipo": c.tipo,
        "empresa_id": c.empresa_id,
        "sede_id": c.sede_id,
        "archivo_url": c.archivo_url,
        "orden": c.orden,
        "activo": c.activo,
    }


# ============================================================
# PANTALLAS
# ============================================================

@router.post("/pantallas")
def crear_pantalla(data: PantallaCreate, db: Session = Depends(get_db)):
    token = secrets.token_urlsafe(24)
    pantalla = models.MediaPantalla(
        id=str(uuid.uuid4()),
        nombre=data.nombre,
        sede_id=data.sede_id,
        empresa_id=data.empresa_id,
        token=token,
        intervalo_segundos=data.intervalo_segundos,
    )
    db.add(pantalla)
    db.commit()
    db.refresh(pantalla)
    return JSONResponse(content=pantalla_json(pantalla), headers=CORS_HEADERS)


@router.get("/pantallas")
def listar_pantallas(
    empresa_id: Optional[str] = None,
    sede_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.MediaPantalla).filter_by(activo=True)
    if empresa_id:
        q = q.filter_by(empresa_id=empresa_id)
    if sede_id:
        q = q.filter_by(sede_id=sede_id)
    pantallas = q.order_by(models.MediaPantalla.nombre).all()
    return JSONResponse(content=[pantalla_json(p) for p in pantallas], headers=CORS_HEADERS)


@router.get("/pantallas/{token}")
def get_pantalla_by_token(token: str, db: Session = Depends(get_db)):
    p = db.query(models.MediaPantalla).filter_by(token=token, activo=True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")
    return JSONResponse(content=pantalla_json(p), headers=CORS_HEADERS)


@router.delete("/pantallas/{pantalla_id}")
def eliminar_pantalla(pantalla_id: str, db: Session = Depends(get_db)):
    p = db.query(models.MediaPantalla).filter_by(id=pantalla_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")
    p.activo = False
    db.commit()
    return JSONResponse(content={"ok": True}, headers=CORS_HEADERS)


@router.post("/heartbeat/{token}")
def heartbeat(token: str, db: Session = Depends(get_db)):
    p = db.query(models.MediaPantalla).filter_by(token=token).first()
    if not p:
        raise HTTPException(status_code=404, detail="Token inválido")
    p.ultima_conexion = datetime.utcnow()
    db.commit()
    return JSONResponse(content={"ok": True}, headers=CORS_HEADERS)


# ============================================================
# CONTENIDO (upload)
# ============================================================

@router.post("/contenido")
async def subir_contenido(
    nombre: str = Form(...),
    tipo: str = Form("image"),
    empresa_id: Optional[str] = Form(None),
    sede_id: Optional[str] = Form(None),
    orden: int = Form(0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Guardar archivo
    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(MEDIA_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # URL pública (nginx sirve /media/files/ → /var/www/media/)
    base_url = os.environ.get("API_BASE_URL", "https://api.nextoapp.net")
    archivo_url = f"{base_url}/media/files/{filename}"

    contenido = models.MediaContenido(
        id=str(uuid.uuid4()),
        nombre=nombre,
        tipo=tipo,
        empresa_id=empresa_id,
        sede_id=sede_id,
        archivo_url=archivo_url,
        orden=orden,
    )
    db.add(contenido)
    db.commit()
    db.refresh(contenido)
    return JSONResponse(content=contenido_json(contenido), headers=CORS_HEADERS)


@router.get("/contenido")
def listar_contenido(
    empresa_id: Optional[str] = None,
    sede_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.MediaContenido).filter_by(activo=True)
    if sede_id:
        # contenido específico de la sede O contenido de toda la empresa
        q = q.filter(
            (models.MediaContenido.sede_id == sede_id) |
            (models.MediaContenido.sede_id == None)
        )
    if empresa_id:
        q = q.filter_by(empresa_id=empresa_id)
    items = q.order_by(models.MediaContenido.orden, models.MediaContenido.created_at).all()
    return JSONResponse(content=[contenido_json(c) for c in items], headers=CORS_HEADERS)


@router.delete("/contenido/{contenido_id}")
def eliminar_contenido(contenido_id: str, db: Session = Depends(get_db)):
    c = db.query(models.MediaContenido).filter_by(id=contenido_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    # Eliminar archivo físico
    try:
        filename = c.archivo_url.split("/")[-1]
        filepath = os.path.join(MEDIA_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass
    c.activo = False
    db.commit()
    return JSONResponse(content={"ok": True}, headers=CORS_HEADERS)


# ============================================================
# PLAYLIST — endpoint principal que usan las pantallas
# ============================================================

@router.get("/playlist/{sede_id}")
def get_playlist(sede_id: str, db: Session = Depends(get_db)):
    """
    Retorna la playlist de imágenes/videos para una sede.
    Las pantallas consultan esto cada N minutos para actualizarse.
    """
    # Buscar sede para obtener empresa_id
    from sqlalchemy import text as _text
    row = db.execute(_text("SELECT empresa_id FROM sedes WHERE id = :id"), {"id": sede_id}).fetchone()
    empresa_id = row[0] if row else None

    # Contenido específico de la sede
    items_sede = db.query(models.MediaContenido).filter(
        models.MediaContenido.activo == True,
        models.MediaContenido.sede_id == sede_id,
    ).order_by(models.MediaContenido.orden, models.MediaContenido.created_at).all()

    # Contenido global de la empresa (sin sede específica)
    q_emp = db.query(models.MediaContenido).filter(
        models.MediaContenido.activo == True,
        models.MediaContenido.sede_id == None,
    )
    if empresa_id:
        q_emp = q_emp.filter(models.MediaContenido.empresa_id == empresa_id)
    items_empresa = q_emp.order_by(
        models.MediaContenido.orden, models.MediaContenido.created_at
    ).all()

    # Combinar: primero sede-específico, luego empresa-global
    todos = items_sede + items_empresa

    return JSONResponse(content={
        "sede_id": sede_id,
        "empresa_id": empresa_id,
        "total": len(todos),
        "items": [contenido_json(c) for c in todos],
    }, headers=CORS_HEADERS)


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

@router.get("/files/{filename}")
def get_file(filename: str):
    filepath = os.path.join(MEDIA_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(filepath)
