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

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Conversation Context Management
    CONTEXT_MAX_MESSAGES: int = 10  # Maximum messages to include in context
    CONTEXT_MAX_TOKENS: int = 4000  # Maximum tokens in context window
    TOKEN_ESTIMATE_MULTIPLIER: float = 0.25  # ~4 chars per token

    # Automatic Summarization
    SUMMARIZATION_ENABLED: bool = True  # Enable auto-summarization when approaching token limit
    SUMMARIZATION_THRESHOLD: float = 0.75  # Summarize when X% of token limit reached (0.75 = 75%)
    SUMMARIZATION_TARGET_RATIO: float = 0.50  # Reduce context to X% of max tokens after summarization (0.50 = 50%)
    SUMMARIZATION_MODEL: str = "ollama/llama2"  # Model to use for summarization
    SUMMARIZATION_MIN_MESSAGES: int = 3  # Minimum messages needed before summarization

    # Title Generation
    TITLE_GENERATION_ENABLED: bool = True  # Enable auto-generation of conversation titles
    TITLE_GENERATION_MODEL: str = "ollama/llama3.2:3b"  # Fast, dedicated model for title generation
    TITLE_MAX_LENGTH: int = 30  # Maximum characters in generated title
    TITLE_INPUT_WORDS: int = 50  # Number of words from message to analyze

    # Contextual Routing
    CONTINUITY_BONUS: float = 0.15  # Confidence boost for previous model
    CONTINUITY_ENABLED: bool = True  # Enable contextual routing
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

    # File Upload Settings
    MAX_FILE_SIZE_MB: int = 5
    MAX_FILES_PER_MESSAGE: int = 5
    MAX_TOTAL_SIZE_MB: int = 10
    ALLOWED_MIME_TYPES: list = [
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    # Extraction Settings
    EXTRACTION_TIMEOUT_SECONDS: int = 30
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "en"
    MIN_TEXT_WORDS_FOR_OCR: int = 100

    # Attachment Storage
    ATTACHMENT_EXPIRY_HOURS: int = 24
    ATTACHMENT_CACHE_TTL_SECONDS: int = 3600

    # Token Management
    MAX_ATTACHMENT_WORDS_IN_PROMPT: int = 2000
    TRUNCATE_LONG_ATTACHMENTS: bool = True

    # Vision Model OCR (via LiteLLM/Ollama) - GPU in separate container
    VISION_OCR_ENABLED: bool = False  # Toggle for vision model OCR
    VISION_OCR_MODEL: str = "ollama/qwen2-vl:7b"  # LiteLLM model identifier
    VISION_OCR_BASE_URL: Optional[str] = None  # Ollama base URL (e.g., http://ollama:11434)
    VISION_OCR_TIMEOUT_SECONDS: int = 45  # Per-page timeout for vision model
    VISION_OCR_MAX_RETRIES: int = 1  # Retry on transient failures
    VISION_OCR_PROMPT: str = "Extract all text from this document page. Return only the extracted text, preserving layout and structure as much as possible."

    # OCR Strategy
    OCR_FALLBACK_ENABLED: bool = True  # Fall back to PaddleOCR CPU if vision fails
    PADDLEOCR_USE_GPU: bool = False  # Explicitly set PaddleOCR to CPU-only (no GPU in API container)

    # Voice Transcription Settings
    TRANSCRIPTION_ENABLED: bool = True
    TRANSCRIPTION_MODEL: str = "base"  # faster-whisper model identifier
    TRANSCRIPTION_TIMEOUT_SECONDS: int = 90
    TRANSCRIPTION_MAX_FILE_SIZE_MB: int = 10
    ALLOWED_AUDIO_FORMATS: list = [
        "audio/wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/m4a",
        "audio/webm"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
