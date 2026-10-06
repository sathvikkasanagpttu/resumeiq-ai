import uuid
import asyncio
from typing import Callable, Any, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.audit import BackgroundTask
from app.core.database import SessionLocal
from app.core.logging import logger

class TaskQueue:
    """
    Asynchronous task manager for background document processing,
    batch matching, and RAG ingestion.
    Supports in-process async worker with full DB status lifecycle tracking.
    """
    @classmethod
    def create_task(
        cls,
        db: Session,
        task_type: str,
        user_id: Optional[str] = None
    ) -> BackgroundTask:
        task = BackgroundTask(
            task_type=task_type,
            user_id=user_id,
            status="pending",
            progress=0.0
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @classmethod
    def update_status(
        cls,
        task_id: str,
        status: str,
        progress: float = 0.0,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        with SessionLocal() as db:
            task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
            if task:
                task.status = status
                task.progress = progress
                if result:
                    task.result = result
                if error:
                    task.error = {"error": error}
                task.updated_at = datetime.now(timezone.utc)
                db.commit()

    @classmethod
    async def run_async_job(
        cls,
        task_id: str,
        job_func: Callable[..., Any],
        *args,
        **kwargs
    ):
        cls.update_status(task_id, status="processing", progress=0.2)
        try:
            if asyncio.iscoroutinefunction(job_func):
                res = await job_func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                res = await loop.run_in_executor(None, lambda: job_func(*args, **kwargs))
            
            cls.update_status(task_id, status="completed", progress=1.0, result={"data": str(res)})
            logger.info(f"Background task {task_id} completed successfully.")
        except Exception as e:
            logger.error(f"Background task {task_id} failed: {e}")
            cls.update_status(task_id, status="failed", progress=0.0, error=str(e))

task_queue = TaskQueue()
