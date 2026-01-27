from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/empresas", tags=["Empresas"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_empresas(db: Session = Depends(get_db)):
    return db.query(models.Empresa).all()


@router.post("/")
def crear_empresa(empresa: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    nueva = models.Empresa(**empresa.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.put("/{empresa_id}")
def actualizar_empresa(empresa_id: str, empresa: schemas.EmpresaUpdate, db: Session = Depends(get_db)):
    db_empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not db_empresa:
        return {"error": "Empresa no encontrada"}

    for key, value in empresa.dict().items():
        setattr(db_empresa, key, value)

    db.commit()
    db.refresh(db_empresa)
    return db_empresa


@router.delete("/{empresa_id}")
def eliminar_empresa(empresa_id: str, db: Session = Depends(get_db)):
    db_empresa = db.query(models.Empresa).filter(models.Empresa.id == empresa_id).first()
    if not db_empresa:
        return {"error": "Empresa no encontrada"}

    db.delete(db_empresa)
    db.commit()
    return {"message": "Empresa eliminada"}
