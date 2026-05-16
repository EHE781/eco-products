from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./ecoscan.db"  # ← SQLite, no necesita instalación
    OPENFOODFACTS_BASE_URL: str = "https://world.openfoodfacts.org"
    GEMINI_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"  # ← corregido, gemini-3.1 no existe
    GEMINI_TIMEOUT_S: float = 30.0

    model_config = {"env_file": ".env"}


settings = Settings()