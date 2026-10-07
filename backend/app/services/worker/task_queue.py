import uuid
import asyncio
from typing import Callable, Any, Dict, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.audit import BackgroundTask
import app.core.database as db_module
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import ResourceNotFoundError

try:
    import redis
    from rq import Queue
except ImportError:
    redis = None
    Queue = None

def execute_task_wrapper(task_id: str, job_func: Callable[..., Any], *args, **kwargs):
    """
    Worker task executor that handles lifecycle tracking, progress updates,
    and structured JSON result persistence.
    """
    TaskQueue.update_status(task_id, status="processing", progress=0.2)
    try:
        result = job_func(*args, **kwargs)
        # Format structured JSON result
        json_result = result if isinstance(result, (dict, list)) else {"result": result}
        TaskQueue.update_status(task_id, status="completed", progress=1.0, result=json_result)
        logger.info(f"Task {task_id} completed successfully.")
        return json_result
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        TaskQueue.update_status(
            task_id,
            status="failed",
            progress=0.0,
            error={"error": str(e), "error_type": type(e).__name__}
        )
        raise

class TaskQueue:
    """
    Production-grade asynchronous task manager for background processing,
    batch matching, and RAG ingestion.
    Supports Redis Queue (RQ) with separate worker process and in-process fallback,
    with full DB status lifecycle tracking, idempotency, retries, and cancellation.
    """
    @classmethod
    def create_task(
        cls,
        db: Session,
        task_type: str,
        user_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        max_retries: int = 3
    ) -> BackgroundTask:
        # Idempotency check
        if idempotency_key:
            existing = db.query(BackgroundTask).filter(BackgroundTask.idempotency_key == idempotency_key).first()
            if existing:
                logger.info(f"Idempotent task request matched existing task {existing.id} for key {idempotency_key}")
                return existing

        task = BackgroundTask(
            task_type=task_type,
            user_id=user_id,
            status="pending",
            progress=0.0,
            idempotency_key=idempotency_key,
            retry_count=0,
            max_retries=max_retries
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
        result: Optional[Any] = None,
        error: Optional[Any] = None,
        db: Optional[Session] = None
    ):
        def _update(session: Session):
            task = session.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
            if task:
                task.status = status
                task.progress = float(progress)
                if result is not None:
                    task.result = result if isinstance(result, (dict, list)) else {"data": result}
                if error is not None:
                    task.error = {"error": error} if isinstance(error, str) else error
                task.updated_at = datetime.now(timezone.utc)
                session.commit()

        if db:
            _update(db)
        else:
            with db_module.SessionLocal() as session:
                _update(session)

    @classmethod
    def cancel_task(
        cls,
        task_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> BackgroundTask:
        """Cancel a pending or running task."""
        def _cancel(session: Session):
            query = session.query(BackgroundTask).filter(BackgroundTask.id == task_id)
            if user_id:
                query = query.filter(BackgroundTask.user_id == user_id)
            task = query.first()
            if not task:
                raise ResourceNotFoundError(f"Task {task_id} not found.")

            task.status = "cancelled"
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(task)
            return task

        if db:
            return _cancel(db)
        with db_module.SessionLocal() as session:
            return _cancel(session)

    @classmethod
    def retry_task(
        cls,
        task_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> BackgroundTask:
        """Retry a failed or cancelled task with incremented retry count."""
        def _retry(session: Session):
            query = session.query(BackgroundTask).filter(BackgroundTask.id == task_id)
            if user_id:
                query = query.filter(BackgroundTask.user_id == user_id)
            task = query.first()
            if not task:
                raise ResourceNotFoundError(f"Task {task_id} not found.")

            if task.retry_count >= task.max_retries:
                raise ValueError(f"Task {task_id} has exceeded max retries ({task.max_retries}).")

            task.retry_count += 1
            task.status = "pending"
            task.error = None
            task.progress = 0.0
            task.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(task)
            return task

        if db:
            return _retry(db)
        with db_module.SessionLocal() as session:
            return _retry(session)

    @classmethod
    def enqueue(
        cls,
        task_id: str,
        job_func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Optional[str]:
        """
        Enqueues task to Redis RQ if available; otherwise executes in background.
        """
        if redis and Queue and settings.REDIS_URL:
            try:
                conn = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
                conn.ping()
                q = Queue("resumeiq", connection=conn)
                rq_job = q.enqueue(execute_task_wrapper, task_id, job_func, *args, **kwargs)
                logger.info(f"Task {task_id} enqueued to RQ job {rq_job.id}")
                return rq_job.id
            except Exception as e:
                logger.warning(f"Failed to enqueue task {task_id} to Redis RQ ({e}); using async fallback.")

        # In-process asynchronous fallback for local dev and testing
        import threading
        thread = threading.Thread(
            target=execute_task_wrapper,
            args=(task_id, job_func, *args),
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
        return None

task_queue = TaskQueue()
