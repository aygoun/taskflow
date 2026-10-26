from pydantic import BaseModel
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None
    priority: str | None = None
    due_date: str | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    priority: str
    due_date: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
