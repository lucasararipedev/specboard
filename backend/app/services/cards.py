"""Regras dos cards, usadas pela API REST e pelo MCP: status, ordem, etiquetas e atividade automática."""

from itertools import islice

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import utcnow
from ..models import Activity, Card, Project
from ..schemas import CardCreate, CardUpdate

def end_of_column(db: Session, project_id: int, status: str) -> float:
    last = db.scalar(select(func.max(Card.position)).where(Card.project_id == project_id, Card.status == status))
    return (last or 0) + 1


def apply_status(card: Card, status: str) -> None:
    """Mantém started_at/done_at coerentes com o status."""
    if status == "doing" and card.started_at is None:
        card.started_at = utcnow()
    card.done_at = utcnow() if status == "done" else None
    card.status = status


def get_card(db: Session, card_id: int) -> Card:
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(404, f"Card #{card_id} não existe")
    return card


def project_card(db: Session, project: Project, card_id: int) -> Card:
    card = db.get(Card, card_id)
    if card is None or card.project_id != project.id:
        raise HTTPException(404, f"Card #{card_id} não existe neste projeto")
    return card


def has_labels(card: Card, labels: list[str] | None) -> bool:
    """O card tem todas as etiquetas pedidas (sem diferenciar maiúsculas). Lista vazia = sem filtro."""
    if not labels:
        return True
    mine = {label.casefold() for label in card.labels or []}
    return all(label.strip().casefold() in mine for label in labels)


def list_cards(db: Session, project: Project, status: str | None = None, labels: list[str] | None = None) -> list[Card]:
    query = select(Card).where(Card.project_id == project.id).order_by(Card.status, Card.position)
    if status:
        query = query.where(Card.status == status)
    return [c for c in db.scalars(query) if has_labels(c, labels)]


def search_cards(
    db: Session, text: str, project: Project | None = None, labels: list[str] | None = None, limit: int = 20
) -> list[Card]:
    """Busca sem diferenciar maiúsculas em título, descrição e spec_ref (para a IA não duplicar card)."""
    term = f"%{text.lower()}%"
    query = select(Card).where(
        or_(
            func.lower(Card.title).like(term),
            func.lower(Card.description).like(term),
            func.lower(Card.spec_ref).like(term),
        )
    )
    if project:
        query = query.where(Card.project_id == project.id)
    found = (c for c in db.scalars(query.order_by(Card.updated_at.desc())) if has_labels(c, labels))
    return list(islice(found, limit))


def create_card(db: Session, project: Project, body: CardCreate, actor: str) -> Card:
    card = Card(
        project_id=project.id,
        position=end_of_column(db, project.id, body.status),
        **body.model_dump(exclude={"status"}),
    )
    apply_status(card, body.status)
    db.add(card)
    db.flush()
    db.add(
        Activity(
            project_id=project.id,
            card_id=card.id,
            actor=actor,
            kind="created",
            message=f'Criou #{card.id} "{card.title}" em {card.status}',
        )
    )
    project.updated_at = utcnow()
    db.commit()
    return card


def update_card(db: Session, card: Card, body: CardUpdate, actor: str) -> Card:
    """Edita qualquer campo. Mudar o status registra uma atividade automaticamente."""
    changes = body.model_dump(exclude_unset=True)
    new_status = changes.pop("status", None)
    position = changes.pop("position", None)
    # due_date aceita null para limpar; os demais campos ignoram null.
    changes = {k: v for k, v in changes.items() if v is not None or k == "due_date"}

    for field, value in changes.items():
        setattr(card, field, value)

    if new_status and new_status != card.status:
        old = card.status
        apply_status(card, new_status)
        if position is None:
            position = end_of_column(db, card.project_id, new_status)
        db.add(
            Activity(
                project_id=card.project_id,
                card_id=card.id,
                actor=actor,
                kind="status",
                message=f'#{card.id} "{card.title}": {old} → {new_status}',
            )
        )
    if position is not None:
        card.position = position

    card.updated_at = utcnow()
    card.project.updated_at = utcnow()
    db.commit()
    return card


def delete_card(db: Session, card: Card, actor: str) -> None:
    db.add(
        Activity(project_id=card.project_id, actor=actor, kind="deleted", message=f'Apagou #{card.id} "{card.title}"')
    )
    db.delete(card)
    db.commit()
