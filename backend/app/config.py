"""Application configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    APP_NAME: str = "AIDI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://aidi:password@localhost:5432/aidi"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Models
#    TEXT_MODEL: str = "ollama/llama3.2:8b"
#    CLASSIFIER_MODEL: str = "ollama/llama3.2:3b"
    TEXT_MODEL: str = "ollama/llama2"
    CLASSIFIER_MODEL: str = "ollama/llama2"


    # Routing
    RULE_CONFIDENCE_THRESHOLD: float = 0.80
    LLM_CONFIDENCE_THRESHOLD: float = 0.60

    # Tools
    TOOLS_ENABLED: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
