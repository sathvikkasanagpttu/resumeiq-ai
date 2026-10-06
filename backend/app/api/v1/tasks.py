from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.audit import BackgroundTask
from app.schemas.common import TaskStatusResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

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

    return TaskStatusResponse(
        task_id=task.id,
        task_type=task.task_type,
        status=task.status,
        progress=task.progress,
        result=task.result,
        error=task.error.get("error") if task.error else None,
        created_at=task.created_at,
        updated_at=task.updated_at
    )
