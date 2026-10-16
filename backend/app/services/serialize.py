"""Converte modelos em respostas, já com os links que a IA repassa ao usuário."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import STATUSES, Activity, Card, Project, Question
from ..schemas import ActivityOut, CardOut, ProjectDetail, ProjectOut, QuestionOut


def project_url(settings: Settings, slug: str) -> str:
    return f"{settings.public_url}/p/{slug}"


def card_url(settings: Settings, slug: str, card_id: int) -> str:
    return f"{project_url(settings, slug)}?card={card_id}"


def questions_url(settings: Settings, slug: str, question_id: int | None = None) -> str:
    url = f"{project_url(settings, slug)}?tab=perguntas"
    return f"{url}&q={question_id}" if question_id else url


def open_question_count(db: Session, project_id: int) -> int:
    return db.scalar(
        select(func.count()).where(Question.project_id == project_id, Question.status == "open")
    )


def status_counts(db: Session, project_id: int) -> dict[str, int]:
    rows = db.execute(
        select(Card.status, func.count()).where(Card.project_id == project_id).group_by(Card.status)
    ).all()
    counts = dict.fromkeys(STATUSES, 0)
    counts.update({status: n for status, n in rows})
    return counts


def project_out(db: Session, settings: Settings, project: Project, detail: bool = False):
    data = dict(
        id=project.id,
        slug=project.slug,
        name=project.name,
        summary=project.summary,
        repo=project.repo,
        archived=project.archived,
        url=project_url(settings, project.slug),
        counts=status_counts(db, project.id),
        open_questions=open_question_count(db, project.id),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
    return ProjectDetail(**data, spec=project.spec) if detail else ProjectOut(**data)


def card_out(settings: Settings, card: Card) -> CardOut:
    slug = card.project.slug
    return CardOut(
        id=card.id,
        project=slug,
        title=card.title,
        description=card.description,
        status=card.status,
        priority=card.priority,
        position=card.position,
        labels=card.labels or [],
        spec_ref=card.spec_ref,
        due_date=card.due_date,
        url=card_url(settings, slug, card.id),
        created_at=card.created_at,
        updated_at=card.updated_at,
        started_at=card.started_at,
        done_at=card.done_at,
    )


def question_out(settings: Settings, q: Question) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        project=q.project.slug,
        card_id=q.card_id,
        question=q.question,
        context=q.context,
        options=q.options or [],
        answer=q.answer,
        status=q.status,
        asked_by=q.asked_by,
        url=questions_url(settings, q.project.slug, q.id),
        created_at=q.created_at,
        answered_at=q.answered_at,
    )


def activity_out(activity: Activity) -> ActivityOut:
    return ActivityOut(
        id=activity.id,
        project=activity.project.slug,
        card_id=activity.card_id,
        actor=activity.actor,
        kind=activity.kind,
        message=activity.message,
        created_at=activity.created_at,
    )
