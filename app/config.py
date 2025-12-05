"""
Configuration management using Pydantic Settings
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Parul University Admission AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # LiveKit Configuration
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    # AI Provider API Keys
    GROQ_API_KEY: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: Optional[str] = None

    # Agent Configuration
    STT_MODEL: str = "whisper-large-v3-turbo"
    LLM_MODEL: str = "llama-3.1-8b-instant"
    TTS_MODEL: str = "tts-1"
    TTS_VOICE: str = "alloy"
    TTS_SPEED: float = 1.1
    LLM_TEMPERATURE: float = 0.7

    # Memory Configuration
    MEMORY_FILE_PATH: str = "./app/memory/conversations.json"
    USER_MEMORY_FILE_PATH: str = "./app/memory/users.json"

    # Data Configuration
    DATA_DIR: str = "./app/data"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # CORS Configuration
    ALLOWED_ORIGINS: Union[list[str], str] = ["http://localhost:5173", "http://localhost:3000","https://calling-voice-ai-be-1.onrender.com"]

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
