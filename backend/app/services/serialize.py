"""Converte modelos em respostas, já com os links que a IA repassa ao usuário."""

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import STATUSES, Activity, AgentSession, Card, Project, Question
from ..schemas import ActivityOut, CardOut, ProjectDetail, ProjectOut, QuestionOut, SessionOut

# Sessão sem sinal de vida há mais que isso aparece como parada no painel Agora.
IDLE_AFTER = timedelta(minutes=15)


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


def label_counts(db: Session, project_id: int) -> dict[str, int]:
    """Etiquetas em uso no projeto, da mais usada para a menos (a IA reaproveita em vez de inventar variações)."""
    rows = db.scalars(select(Card.labels).where(Card.project_id == project_id))
    counter = Counter(label for labels in rows for label in labels or [])
    return dict(counter.most_common())


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
    if detail:
        return ProjectDetail(**data, spec=project.spec, labels=label_counts(db, project.id))
    return ProjectOut(**data)


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


def session_out(settings: Settings, session: AgentSession, now: datetime | None = None) -> SessionOut:
    now = now or datetime.now(timezone.utc)
    slug = session.project.slug if session.project else None
    card = session.card
    return SessionOut(
        key=session.key,
        actor=session.actor,
        client=session.client,
        project=slug,
        project_url=project_url(settings, slug) if slug else None,
        cwd=session.cwd,
        doing=session.doing,
        card_id=card.id if card else None,
        card_title=card.title if card else None,
        card_url=card_url(settings, card.project.slug, card.id) if card else None,
        active=session.active,
        idle=now - session.last_seen_at > IDLE_AFTER,
        started_at=session.started_at,
        last_seen_at=session.last_seen_at,
        ended_at=session.ended_at,
    )
