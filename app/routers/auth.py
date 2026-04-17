import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from app.database import SessionLocal
from passlib.hash import bcrypt as ph

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class UsuarioLoginOut(BaseModel):
    id: str
    nombre: str
    apellido: Optional[str] = None
    username: str
    email: Optional[str] = None
    rol: str
    perfil: str
    puede_crear: bool
    puede_editar: bool
    puede_borrar: bool
    empresa_id: Optional[str] = None
    sede_id: Optional[str] = None
    activo: bool


# ── POST /auth/login ────────────────────────────────────────
@router.post("/login", response_model=UsuarioLoginOut)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM usuarios WHERE username = :u AND activo = true"),
        {"u": data.username}
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # Verificar contraseña (bcrypt o plana para legacy)
    try:
        ok = ph.verify(data.password, row["password"])
    except Exception:
        ok = (data.password == row["password"])

    if not ok:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # Verificar contrato activo (solo para usuarios no master_admin)
    rol = row.get("rol") or row.get("perfil") or "operador"
    if rol != "master_admin" and row.get("empresa_id"):
        contrato = db.execute(text("""
            SELECT fecha_fin, activo FROM contratos
            WHERE empresa_id = :eid AND activo = true
            ORDER BY fecha_fin DESC LIMIT 1
        """), {"eid": row["empresa_id"]}).mappings().fetchone()

        if contrato:
            from datetime import date
            if contrato["fecha_fin"] < date.today():
                raise HTTPException(
                    status_code=403,
                    detail="Contrato vencido. Por favor contacte al administrador de NEXTO."
                )

    return UsuarioLoginOut(
        id=row["id"],
        nombre=row["nombre"],
        apellido=row.get("apellido"),
        username=row["username"],
        email=row.get("email"),
        rol=rol,
        perfil=row.get("perfil") or "operador",
        puede_crear=bool(row.get("puede_crear", False)),
        puede_editar=bool(row.get("puede_editar", False)),
        puede_borrar=bool(row.get("puede_borrar", False)),
        empresa_id=row.get("empresa_id"),
        sede_id=row.get("sede_id"),
        activo=bool(row.get("activo", True)),
    )


# ── GET /auth/contrato/{empresa_id} ────────────────────────
@router.get("/contrato/{empresa_id}")
def get_contrato(empresa_id: str, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT * FROM contratos
        WHERE empresa_id = :eid AND activo = true
        ORDER BY fecha_fin DESC LIMIT 1
    """), {"eid": empresa_id}).mappings().fetchone()

    if not row:
        return {"tiene_contrato": False}

    from datetime import date
    vigente = row["fecha_fin"] >= date.today()
    return {
        "tiene_contrato": True,
        "vigente": vigente,
        "fecha_inicio": str(row["fecha_inicio"]),
        "fecha_fin": str(row["fecha_fin"]),
        "max_sedes": row["max_sedes"],
        "modulos": row["modulos"] or {},
    }


# ── POST /auth/contrato ─────────────────────────────────────
class ContratoIn(BaseModel):
    empresa_id: str
    fecha_inicio: str
    fecha_fin: str
    max_sedes: int = 1
    modulos: dict = {}


@router.post("/contrato", status_code=201)
def crear_contrato(data: ContratoIn, db: Session = Depends(get_db)):
    import json
    # Desactivar contratos anteriores
    db.execute(text(
        "UPDATE contratos SET activo = false WHERE empresa_id = :eid"
    ), {"eid": data.empresa_id})
    db.execute(text("""
        INSERT INTO contratos (id, empresa_id, fecha_inicio, fecha_fin, max_sedes, modulos, activo)
        VALUES (:id, :eid, :fi, :ff, :ms, :mod::jsonb, true)
    """), {
        "id": str(uuid.uuid4()),
        "eid": data.empresa_id,
        "fi": data.fecha_inicio,
        "ff": data.fecha_fin,
        "ms": data.max_sedes,
        "mod": json.dumps(data.modulos),
    })
    db.commit()
    return {"status": "ok"}


# ── PUT /auth/usuario/{id}/permisos ─────────────────────────
class PermisosIn(BaseModel):
    rol: Optional[str] = None
    puede_crear: Optional[bool] = None
    puede_editar: Optional[bool] = None
    puede_borrar: Optional[bool] = None
    activo: Optional[bool] = None
    email: Optional[str] = None


@router.put("/usuario/{usuario_id}/permisos")
def actualizar_permisos(usuario_id: str, data: PermisosIn, db: Session = Depends(get_db)):
    sets = []
    params = {"id": usuario_id}
    if data.rol is not None:
        sets.append("rol = :rol"); params["rol"] = data.rol
    if data.puede_crear is not None:
        sets.append("puede_crear = :pc"); params["pc"] = data.puede_crear
    if data.puede_editar is not None:
        sets.append("puede_editar = :pe"); params["pe"] = data.puede_editar
    if data.puede_borrar is not None:
        sets.append("puede_borrar = :pb"); params["pb"] = data.puede_borrar
    if data.activo is not None:
        sets.append("activo = :activo"); params["activo"] = data.activo
    if data.email is not None:
        sets.append("email = :email"); params["email"] = data.email
    if not sets:
        return {"status": "no changes"}
    db.execute(text(f"UPDATE usuarios SET {', '.join(sets)} WHERE id = :id"), params)
    db.commit()
    return {"status": "ok"}
