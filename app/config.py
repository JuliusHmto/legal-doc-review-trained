"""
Legal Document Review System - Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    
    # PostgreSQL Configuration
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/legal_doc_review"
    
    # Alternative PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "legal_doc_review"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    
    # File Upload Settings
    upload_dir: str = "storage/uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = ["pdf", "docx", "txt", "doc"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL for SQLAlchemy."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
