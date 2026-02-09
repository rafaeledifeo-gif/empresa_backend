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
    pool_pre_ping=True,      # 🔥 Repara conexiones muertas automáticamente
    pool_recycle=180,        # 🔥 Recicla conexiones cada 3 minutos
    pool_size=5,             # 🔥 Tamaño ideal para plan gratuito
    max_overflow=0,          # 🔥 Evita saturar la base de datos
)

# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================================
# BASE
# ============================================================

Base = declarative_base()
