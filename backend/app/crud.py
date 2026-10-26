from sqlalchemy.orm import Session
from . import models


def _normalize_tag(name: str) -> str:
    """Normalize a tag name by stripping whitespace and lowercasing."""
    return name.strip().lower()


def get_or_create_tag(db: Session, name: str) -> models.Tag:
    """Look up a tag by its normalized name; create it if it doesn't exist."""
    normalized = _normalize_tag(name)
    tag = db.query(models.Tag).filter(models.Tag.name == normalized).first()
    if tag is None:
        tag = models.Tag(name=normalized)
        db.add(tag)
        db.flush()  # assign an id without committing
    return tag


def _resolve_tags(db: Session, tag_names: list[str]) -> list[models.Tag]:
    """Normalize, dedupe (preserving first-occurrence order), drop empties,
    and return a list of Tag ORM objects."""
    seen: set[str] = set()
    tags: list[models.Tag] = []
    for raw in tag_names:
        normalized = _normalize_tag(raw)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        tags.append(get_or_create_tag(db, normalized))
    return tags


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    completed: bool | None = None,
    priority: str | None = None,
    tag: str | None = None,
):
    query = db.query(models.Task)
    if completed is not None:
        query = query.filter(models.Task.completed == completed)
    if priority is not None:
        query = query.filter(models.Task.priority == priority)
    if tag is not None:
        query = query.join(models.Task.tags).filter(models.Tag.name == tag.strip().lower())
    return query.order_by(models.Task.created_at.desc()).offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def create_task(
    db: Session,
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str | None = None,
    tags: list[str] | None = None,
):
    db_task = models.Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
    )
    db.add(db_task)
    db.flush()  # assign id so we can set tags before commit
    if tags:
        db_task.tags = _resolve_tags(db, tags)
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
    tags: list[str] | None = None,
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
    if tags is not None:
        db_task.tags = _resolve_tags(db, tags)
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
        .outerjoin(models.Task.tags)
        .filter(
            (models.Task.title.ilike(f"%{query}%"))
            | (models.Task.description.ilike(f"%{query}%"))
            | (models.Tag.name.ilike(f"%{query}%"))
        )
        .distinct()
        .all()
    )


def get_all_tags(db: Session):
    return db.query(models.Tag).order_by(models.Tag.name).all()
