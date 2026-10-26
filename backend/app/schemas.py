from pydantic import BaseModel, field_serializer
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str | None = None
    tags: list[str] = []


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None
    priority: str | None = None
    due_date: str | None = None
    tags: list[str] | None = None


class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    priority: str
    due_date: str | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagResponse] = []

    @field_serializer('tags')
    def serialize_tags(self, tags: list[TagResponse]) -> list[str]:
        return [t.name for t in tags]

    class Config:
        from_attributes = True
