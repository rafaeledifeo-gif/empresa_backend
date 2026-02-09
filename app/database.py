from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ============================================================
# DATABASE URL (Render)
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

# ============================================================
# ENGINE CONFIGURADO PARA RENDER FREE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=180,
    pool_size=5,
    max_overflow=0,
)

# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================
# BASE
# ============================================================

Base = declarative_base()

# ============================================================
# ⭐ FUNCIÓN get_db (NECESARIA PARA TODOS LOS ROUTERS)
# ============================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
