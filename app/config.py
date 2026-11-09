import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/dx_order"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
