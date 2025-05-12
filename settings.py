#setings.py
from pydantic_settings import BaseSettings
import os
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploaded_photos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Settings(BaseSettings):
    ENV: str = "development"

    @property
    def DATABASE_URL(self):
        if self.ENV == "testing":
            return "sqlite:///./test.db"
        return "postgresql://administrator:5034!@localhost:5432/postgres"

settings = Settings()
