import sys
import os
from app.core.config import settings
from app.core.logging import logger

def start_worker():
    """
    Entrypoint for standalone background worker service.
    Connects to Redis and processes tasks from the 'resumeiq' queue.
    """
    try:
        import redis
        from rq import Worker, Queue
    except ImportError:
        logger.error("RQ or Redis not installed. Cannot start worker.")
        sys.exit(1)

    redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
    logger.info(f"Starting ResumeIQ background RQ worker connecting to: {redis_url}")

    try:
        conn = redis.Redis.from_url(redis_url)
        conn.ping()
        logger.info("Successfully connected to Redis. Listening for jobs on queues: ['resumeiq', 'default']...")
        queues = [Queue("resumeiq", connection=conn), Queue("default", connection=conn)]
        worker = Worker(queues, connection=conn)
        worker.work(with_scheduler=True)
    except Exception as e:
        logger.error(f"Worker encountered fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_worker()
