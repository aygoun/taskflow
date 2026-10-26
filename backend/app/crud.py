from sqlalchemy import case
from sqlalchemy.orm import Session
from . import models

_ALLOWED_SORT_FIELDS = {"priority", "title", "due_date", "created_at", "completed"}
_ALLOWED_SORT_ORDERS = {"asc", "desc"}


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    completed: bool | None = None,
    priority: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    # Validate sort parameters, falling back to defaults for invalid values
    if sort_by not in _ALLOWED_SORT_FIELDS:
        sort_by = "created_at"
    if sort_order not in _ALLOWED_SORT_ORDERS:
        sort_order = "desc"

    query = db.query(models.Task)
    if completed is not None:
        query = query.filter(models.Task.completed == completed)
    if priority is not None:
        query = query.filter(models.Task.priority == priority)

    # Build the ORDER BY clause
    if sort_by == "priority":
        # CASE expression so priority sorts as high > medium > low
        # (not alphabetically). Lower case value = higher priority.
        priority_case = case(
            (models.Task.priority == "high", 0),
            (models.Task.priority == "medium", 1),
            (models.Task.priority == "low", 2),
            else_=3,
        )
        # desc = high first → ascending case values (0, 1, 2)
        # asc  = low first  → descending case values (2, 1, 0)
        order_column = priority_case.asc() if sort_order == "desc" else priority_case.desc()
    else:
        column = getattr(models.Task, sort_by)
        order_column = column.desc() if sort_order == "desc" else column.asc()

    return query.order_by(order_column).offset(skip).limit(limit).all()


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
