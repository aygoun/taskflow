from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional

from . import crud, schemas
from .database import init_db, get_db

init_db()

app = FastAPI(title="TaskFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_SORT_BY = {"created_at", "title", "priority", "due_date"}
VALID_SORT_ORDER = {"asc", "desc"}


@app.get("/api/tasks", response_model=list[schemas.TaskResponse])
def list_tasks(
    completed: Optional[bool] = None,
    priority: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    if sort_by not in VALID_SORT_BY:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by '{sort_by}'. Must be one of: {sorted(VALID_SORT_BY)}",
        )
    if sort_order not in VALID_SORT_ORDER:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_order '{sort_order}'. Must be one of: {sorted(VALID_SORT_ORDER)}",
        )
    return crud.get_tasks(
        db,
        skip=skip,
        limit=limit,
        completed=completed,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@app.post("/api/tasks", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    if task.priority not in ("low", "medium", "high"):
        raise HTTPException(status_code=400, detail="Priority must be low, medium, or high")
    return crud.create_task(
        db,
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
    )


@app.get("/api/tasks/search", response_model=list[schemas.TaskResponse])
def search_tasks(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return crud.search_tasks(db, q)


@app.get("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/api/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    if update.priority is not None and update.priority not in ("low", "medium", "high"):
        raise HTTPException(status_code=400, detail="Priority must be low, medium, or high")
    task = crud.update_task(
        db,
        task_id,
        title=update.title,
        description=update.description,
        completed=update.completed,
        priority=update.priority,
        due_date=update.due_date,
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    if not crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
