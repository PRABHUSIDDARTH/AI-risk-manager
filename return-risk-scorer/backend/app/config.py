from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    MODEL_PATH: str = str(Path(__file__).parent.parent.parent / 'ml' / 'model.pkl')
    MODEL_VERSION_PATH: str = str(Path(__file__).parent.parent.parent / 'ml' / 'model_version.txt')
    DATABASE_URL: str = "sqlite:///./return_risk.db"
    SCORE_THRESHOLD_ALLOW: float = 0.35
    SCORE_THRESHOLD_BLOCK: float = 0.65
    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
