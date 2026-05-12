from fastapi import APIRouter, Depends, HTTPException, Path, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from database import SessionLocal
from models import Task
from routers.authentication import get_current_vendor
from typing import Annotated
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

templates = Jinja2Templates(directory="templates")

class TaskRequest(BaseModel):
    title: str
    description: str | None = None
    status: str = "Bekliyor"
    task_type: str = "Genel"

class TaskStatusUpdate(BaseModel):
    status: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
vendor_dependency = Annotated[dict, Depends(get_current_vendor)]

@router.get("/", status_code=status.HTTP_200_OK)
async def render_tasks_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="tasks.html",
        context={"request": request}
    )

@router.get("/api/", status_code=status.HTTP_200_OK)
async def list_tasks(vendor: vendor_dependency, db: db_dependency):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    return db.query(Task).filter(Task.vendor_id == vendor.get('id')).all()

@router.post("/api/", status_code=status.HTTP_201_CREATED)
async def create_task(vendor: vendor_dependency, db: db_dependency, task_request: TaskRequest):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    task = Task(**task_request.dict(), vendor_id=vendor.get('id'))
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/api/{task_id}", status_code=status.HTTP_200_OK)
async def update_task(vendor: vendor_dependency, db: db_dependency, task_request: TaskRequest, task_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    task = db.query(Task).filter(Task.id == task_id).filter(Task.vendor_id == vendor.get('id')).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    task.title = task_request.title
    task.description = task_request.description
    task.status = task_request.status
    task.task_type = task_request.task_type
    
    db.add(task)
    db.commit()
    return task

@router.put("/api/{task_id}/status", status_code=status.HTTP_200_OK)
async def update_task_status(vendor: vendor_dependency, db: db_dependency, status_update: TaskStatusUpdate, task_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    task = db.query(Task).filter(Task.id == task_id).filter(Task.vendor_id == vendor.get('id')).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    task.status = status_update.status
    db.add(task)
    db.commit()
    return task

@router.delete("/api/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(vendor: vendor_dependency, db: db_dependency, task_id: int = Path(gt=0)):
    if vendor is None:
        return RedirectResponse(url="/auth/login", status_code=302)
    task = db.query(Task).filter(Task.id == task_id).filter(Task.vendor_id == vendor.get('id')).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    db.query(Task).filter(Task.id == task_id).delete()
    db.commit()
    return {"message": "Task deleted successfully"}
