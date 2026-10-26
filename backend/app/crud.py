from sqlalchemy.orm import Session
from . import models


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    completed: bool | None = None,
    priority: str | None = None,
):
    query = db.query(models.Task)
    if completed is not None:
        query = query.filter(models.Task.completed == completed)
    if priority is not None:
        query = query.filter(models.Task.priority == priority)
    return query.order_by(models.Task.created_at.desc()).offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def create_task(db: Session, title: str, description: str = "", priority: str = "medium", due_date: str | None = None):
    db_task = models.Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(
    db: Session,
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    completed: bool | None = None,
    priority: str | None = None,
    due_date: str | None = None,
):
    db_task = get_task(db, task_id)
    if db_task is None:
        return None
    if title is not None:
        db_task.title = title
    if description is not None:
        db_task.description = description
    if completed is not None:
        db_task.completed = completed
    if priority is not None:
        db_task.priority = priority
    if due_date is not None:
        db_task.due_date = due_date
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    db_task = get_task(db, task_id)
    if db_task is None:
        return False
    db.delete(db_task)
    db.commit()
    return True


def search_tasks(db: Session, query: str):
    return (
        db.query(models.Task)
        .filter(
            (models.Task.title.ilike(f"%{query}%"))
            | (models.Task.description.ilike(f"%{query}%"))
        )
        .all()
    )
