from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Base

# Tạo engine kết nối PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Khởi tạo Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency cung cấp session database cho từng request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
