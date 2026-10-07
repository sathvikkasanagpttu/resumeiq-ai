import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.main import app
from app.services.worker.task_queue import TaskQueue
from app.models.audit import BackgroundTask
from app.core.config import settings

def get_auth_headers(client: TestClient, email: str = "async_user@example.com"):
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Async Tester",
        "password": "SecurePass123!"
    })
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_health_really_pings_database(client: TestClient):
    """GET /api/v1/health must report real database connection status."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["database_connected"] is True
    assert data["status"] in ("healthy", "degraded")

def test_health_really_pings_redis_false_when_unreachable(client: TestClient):
    """
    GET /api/v1/health must genuinely attempt to ping Redis.
    If REDIS_URL points to an unreachable port, redis_connected must be False,
    never True just because a string exists.
    """
    with patch.object(settings, "REDIS_URL", "redis://127.0.0.1:59999/0"):
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["redis_connected"] is False

def test_health_ready_returns_503_when_database_fails(client: TestClient):
    """GET /api/v1/health/ready must return 503 when the database ping fails."""
    # Mock database failure on SELECT 1
    with patch("sqlalchemy.orm.Session.execute", side_effect=Exception("Database connection down")):
        res = client.get("/api/v1/health/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["database_connected"] is False
        assert data["status"] == "not_ready"

def test_task_queue_idempotency(db_session):
    """Submitting tasks with the same idempotency key must return the existing task without duplicate execution."""
    idempotency_key = "idemp_test_key_12345"
    task1 = TaskQueue.create_task(
        db=db_session,
        task_type="batch_match",
        user_id=None,
        idempotency_key=idempotency_key
    )
    task2 = TaskQueue.create_task(
        db=db_session,
        task_type="batch_match",
        user_id=None,
        idempotency_key=idempotency_key
    )
    assert task1.id == task2.id
    assert task2.idempotency_key == idempotency_key

def test_task_queue_persists_real_json_result(db_session):
    """Task results must be persisted as structured JSON dict, not str(res)."""
    task = TaskQueue.create_task(db=db_session, task_type="doc_parse")
    
    # Simulate job execution returning a dictionary
    mock_result = {
        "candidate_name": "Alice Smith",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "score": 94.5
    }
    TaskQueue.update_status(task_id=task.id, status="completed", progress=1.0, result=mock_result, db=db_session)
    
    fetched = db_session.query(BackgroundTask).filter(BackgroundTask.id == task.id).first()
    assert fetched.status == "completed"
    assert fetched.progress == 1.0
    assert fetched.result == mock_result
    assert isinstance(fetched.result, dict)
    assert fetched.result["skills"] == ["Python", "FastAPI", "PostgreSQL"]

def test_task_cancellation_and_retry(client: TestClient, db_session):
    """Tasks can be cancelled and failed tasks can be retried with incremented retry count."""
    headers = get_auth_headers(client, "task_user@example.com")
    task = TaskQueue.create_task(db=db_session, task_type="long_rag_ingest")
    
    # 1. Cancel task via API
    res = client.post(f"/api/v1/tasks/{task.id}/cancel", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "cancelled"

    # 2. Mark as failed and retry
    TaskQueue.update_status(task_id=task.id, status="failed", error="Temporary network timeout")
    res_retry = client.post(f"/api/v1/tasks/{task.id}/retry", headers=headers)
    assert res_retry.status_code == 200
    data = res_retry.json()
    assert data["status"] in ("pending", "processing")
    assert data["retry_count"] == 1
