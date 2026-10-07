from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.audit import BackgroundTask
from app.schemas.common import TaskStatusResponse
from app.services.worker.task_queue import TaskQueue
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

def _to_response(task: BackgroundTask) -> TaskStatusResponse:
    return TaskStatusResponse(
        task_id=task.id,
        task_type=task.task_type,
        status=task.status,
        progress=task.progress or 0.0,
        result=task.result,
        error=task.error.get("error") if isinstance(task.error, dict) else (task.error or None),
        idempotency_key=task.idempotency_key,
        retry_count=task.retry_count or 0,
        max_retries=task.max_retries or 3,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id and task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return _to_response(task)

@router.post("/{task_id}/cancel", response_model=TaskStatusResponse)
def cancel_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id and task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    cancelled_task = TaskQueue.cancel_task(task_id=task_id, db=db)
    return _to_response(cancelled_task)

@router.post("/{task_id}/retry", response_model=TaskStatusResponse)
def retry_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id and task.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        retried_task = TaskQueue.retry_task(task_id=task_id, db=db)
        return _to_response(retried_task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

