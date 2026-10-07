import time
import threading
from typing import Dict, List, Optional, Tuple
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.logging import logger

try:
    import redis
except ImportError:
    redis = None

class RateLimiter:
    """
    Production-grade rate limiter supporting Redis with automatic in-memory fallback.
    Implements a sliding window log/counter.
    """
    def __init__(self):
        self._redis_client = None
        self._redis_available = False
        self._memory_store: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._init_redis()

    def _init_redis(self):
        if redis and settings.REDIS_URL:
            try:
                client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
                client.ping()
                self._redis_client = client
                self._redis_available = True
                logger.info("RateLimiter initialized with Redis backend.")
            except Exception as e:
                logger.warning(f"RateLimiter could not connect to Redis ({e}); falling back to memory.")
                self._redis_available = False
        else:
            self._redis_available = False

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        Returns (is_limited, remaining_attempts, retry_after_seconds).
        """
        now = time.time()
        
        # Try Redis if available
        if self._redis_available and self._redis_client:
            try:
                pipe = self._redis_client.pipeline()
                redis_key = f"rl:{key}"
                # Remove timestamps older than window
                pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
                # Count elements in window
                pipe.zcard(redis_key)
                # Add current timestamp
                pipe.zadd(redis_key, {str(now): now})
                # Set TTL
                pipe.expire(redis_key, window_seconds)
                results = pipe.execute()
                
                count = results[1]
                if count >= max_requests:
                    return True, 0, window_seconds
                return False, max(0, max_requests - count - 1), 0
            except Exception as e:
                logger.warning(f"Redis rate-limit error ({e}), using memory fallback.")

        # In-memory fallback
        with self._lock:
            timestamps = self._memory_store.get(key, [])
            cutoff = now - window_seconds
            valid_timestamps = [t for t in timestamps if t > cutoff]
            
            if len(valid_timestamps) >= max_requests:
                oldest = valid_timestamps[0]
                retry_after = int(max(1, window_seconds - (now - oldest)))
                self._memory_store[key] = valid_timestamps
                return True, 0, retry_after
            
            valid_timestamps.append(now)
            self._memory_store[key] = valid_timestamps
            remaining = max(0, max_requests - len(valid_timestamps))
            return False, remaining, 0

    def record_failure(self, key: str, max_failures: int = 5, window_seconds: int = 300) -> bool:
        """
        Record a failure and return True if threshold exceeded.
        """
        is_limited, _, _ = self.is_rate_limited(f"fail:{key}", max_failures, window_seconds)
        return is_limited

    def is_failed_locked(self, key: str, max_failures: int = 5, window_seconds: int = 300) -> Tuple[bool, int]:
        """
        Check if currently locked out due to previous failures without recording a new hit.
        """
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            timestamps = self._memory_store.get(f"fail:{key}", [])
            valid = [t for t in timestamps if t > cutoff]
            self._memory_store[f"fail:{key}"] = valid
            if len(valid) >= max_failures:
                oldest = valid[0]
                retry_after = int(max(1, window_seconds - (now - oldest)))
                return True, retry_after
            return False, 0

    def clear_failures(self, key: str):
        fail_key = f"fail:{key}"
        if self._redis_available and self._redis_client:
            try:
                self._redis_client.delete(f"rl:{fail_key}")
            except Exception:
                pass
        with self._lock:
            if fail_key in self._memory_store:
                del self._memory_store[fail_key]

    def check_or_raise(self, key: str, max_requests: int, window_seconds: int, action_name: str = "request"):
        is_limited, remaining, retry_after = self.is_rate_limited(key, max_requests, window_seconds)
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {action_name}. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

rate_limiter = RateLimiter()
