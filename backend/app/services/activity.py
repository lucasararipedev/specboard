"""Histórico do projeto: notas e decisões registradas à mão (as automáticas nascem em cada serviço)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import utcnow
from ..models import Activity, Project
from ..schemas import ActivityCreate
from .cards import project_card


def list_activity(db: Session, project: Project, limit: int = 50, card_id: int | None = None) -> list[Activity]:
    query = select(Activity).where(Activity.project_id == project.id)
    if card_id is not None:
        query = query.where(Activity.card_id == card_id)
    query = query.order_by(Activity.created_at.desc(), Activity.id.desc()).limit(limit)
    return list(db.scalars(query))


def log_activity(db: Session, project: Project, body: ActivityCreate, actor: str) -> Activity:
    if body.card_id is not None:
        project_card(db, project, body.card_id)
    activity = Activity(project_id=project.id, actor=actor, **body.model_dump())
    db.add(activity)
    project.updated_at = utcnow()
    db.commit()
    return activity
