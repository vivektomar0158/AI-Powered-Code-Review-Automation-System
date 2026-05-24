import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Code Reviewer"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-this-to-a-secure-random-string-in-production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://reviewer:password@localhost:5432/code_reviewer"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # LLM APIs
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "code-review-patterns"
    PINECONE_ENVIRONMENT: str = "us-east-1"

    # GitHub App
    GITHUB_APP_ID: int = 0
    GITHUB_PRIVATE_KEY_PATH: str = "./github-app-key.pem"
    GITHUB_PRIVATE_KEY_BASE64: str = ""
    GITHUB_WEBHOOK_SECRET: str = "generate-with-openssl-rand-hex-32"

    # Cost Controls
    MAX_REVIEWS_PER_HOUR: int = 100
    MAX_COST_PER_DAY_USD: float = 10.00
    COST_ALERT_THRESHOLD_PERCENT: float = 80.0

    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "console"

    # Agent Config
    AGENT_TIMEOUT_SECONDS: int = 60
    REVIEW_TIMEOUT_SECONDS: int = 300
    MAX_FILES_FOR_PERFORMANCE_AGENT: int = 100
    EMBEDDING_CACHE_TTL_SECONDS: int = 604800

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    def get_github_private_key(self) -> str:
        """Helper to get private key from either base64 env var or file path."""
        if self.GITHUB_PRIVATE_KEY_BASE64:
            import base64
            return base64.b64decode(self.GITHUB_PRIVATE_KEY_BASE64).decode("utf-8")
        elif self.GITHUB_PRIVATE_KEY_PATH and os.path.exists(self.GITHUB_PRIVATE_KEY_PATH):
            with open(self.GITHUB_PRIVATE_KEY_PATH, "r") as f:
                return f.read()
        return ""

settings = Settings()
