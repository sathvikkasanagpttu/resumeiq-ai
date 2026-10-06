import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "RESUMEIQ"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "resumeiq-super-secret-jwt-key-2026-production-grade")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./resumeiq.db"  # Defaults to local SQLite for instant zero-dependency execution, override with postgresql+psycopg2://...
    )
    
    # Redis
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    
    # AI / LLM Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    USE_FALLBACK_DENSE_EMBEDDINGS: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    # File upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt"]
    
    # Default Compatibility Scoring Weights
    WEIGHT_REQUIRED_SKILLS: float = 0.25
    WEIGHT_SEMANTIC_FIT: float = 0.20
    WEIGHT_EVIDENCE_STRENGTH: float = 0.15
    WEIGHT_EXPERIENCE_ALIGNMENT: float = 0.15
    WEIGHT_PREFERRED_SKILLS: float = 0.08
    WEIGHT_SENIORITY_ALIGNMENT: float = 0.07
    WEIGHT_DOMAIN_ALIGNMENT: float = 0.05
    WEIGHT_EDUCATION_ALIGNMENT: float = 0.05
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
