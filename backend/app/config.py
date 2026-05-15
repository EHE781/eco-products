from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://localhost/ecoscan"
    OPENFOODFACTS_BASE_URL: str = "https://world.openfoodfacts.org"
    GEMINI_KEY: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
