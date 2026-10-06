from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    database_connected: bool
    ai_engine_ready: bool
    redis_connected: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskStatusResponse(BaseModel):
    task_id: str
    task_type: str
    status: str  # pending, processing, completed, failed
    progress: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
