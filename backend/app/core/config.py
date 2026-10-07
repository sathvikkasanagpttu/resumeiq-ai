import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator

INSECURE_DEFAULT_KEYS = {
    "resumeiq-super-secret-jwt-key-2026-production-grade",
    "resumeiq-production-secret-jwt-key-2026",
    "secret",
    "changeme",
    "default",
    ""
}

class Settings(BaseSettings):
    PROJECT_NAME: str = "RESUMEIQ"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    SECRET_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("SECRET_KEY", None))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    EXTENSION_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes for browser extension access tokens
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", 
            "sqlite:///./resumeiq.db"
        )
    )
    
    # Redis
    REDIS_URL: Optional[str] = Field(default_factory=lambda: os.getenv("REDIS_URL", None))
    
    # AI / LLM Configuration
    GEMINI_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", None))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    EMBEDDING_MODEL: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-004"))
    USE_FALLBACK_DENSE_EMBEDDINGS: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    CHROME_EXTENSION_ID: Optional[str] = Field(default_factory=lambda: os.getenv("CHROME_EXTENSION_ID", None))
    
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

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        env = (self.ENVIRONMENT or "").lower()
        key = self.SECRET_KEY or ""
        
        if env in ("production", "prod"):
            if not key or key in INSECURE_DEFAULT_KEYS or len(key) < 32:
                raise ValueError(
                    "CRITICAL SECURITY: In production mode, SECRET_KEY must be explicitly set "
                    "to a cryptographically secure random value of at least 32 characters."
                )
            # Remove any wildcard origins in production
            self.BACKEND_CORS_ORIGINS = [o for o in self.BACKEND_CORS_ORIGINS if o != "*"]
        else:
            if not key:
                self.SECRET_KEY = "dev-insecure-secret-key-32-characters-minimum!!"
                
        # Register extension origin if extension ID is configured
        if self.CHROME_EXTENSION_ID:
            ext_origin = f"chrome-extension://{self.CHROME_EXTENSION_ID}"
            if ext_origin not in self.BACKEND_CORS_ORIGINS:
                self.BACKEND_CORS_ORIGINS.append(ext_origin)
                
        return self

settings = Settings()
