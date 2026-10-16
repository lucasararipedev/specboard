from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..db import utcnow
from ..deps import card_or_404, get_actor, get_db, get_settings, project_or_404, require_token
from ..models import Activity, Card
from ..schemas import CardCreate, CardOut, CardUpdate, Status
from ..services.serialize import card_out

router = APIRouter(prefix="/api", tags=["cards"], dependencies=[Depends(require_token)])


def end_of_column(db: Session, project_id: int, status: str) -> float:
    last = db.scalar(select(func.max(Card.position)).where(Card.project_id == project_id, Card.status == status))
    return (last or 0) + 1


def apply_status(card: Card, status: str) -> None:
    """Mantém started_at/done_at coerentes com o status."""
    if status == "doing" and card.started_at is None:
        card.started_at = utcnow()
    card.done_at = utcnow() if status == "done" else None
    card.status = status


@router.get("/projects/{slug}/cards", response_model=list[CardOut])
def list_cards(
    slug: str,
    status: Status | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    project = project_or_404(db, slug)
    query = select(Card).where(Card.project_id == project.id).order_by(Card.status, Card.position)
    if status:
        query = query.where(Card.status == status)
    return [card_out(settings, c) for c in db.scalars(query)]


@router.post("/projects/{slug}/cards", response_model=CardOut, status_code=201)
def create_card(
    slug: str,
    body: CardCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    project = project_or_404(db, slug)
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
    return card_out(settings, card)


@router.get("/cards/{card_id}", response_model=CardOut)
def get_card(card_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return card_out(settings, card_or_404(db, card_id))


@router.patch("/cards/{card_id}", response_model=CardOut)
def update_card(
    card_id: int,
    body: CardUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    """Edita qualquer campo. Mudar o status registra uma atividade automaticamente."""
    card = card_or_404(db, card_id)
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
    return card_out(settings, card)


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: int, db: Session = Depends(get_db), actor: str = Depends(get_actor)):
    card = card_or_404(db, card_id)
    db.add(
        Activity(project_id=card.project_id, actor=actor, kind="deleted", message=f'Apagou #{card.id} "{card.title}"')
    )
    db.delete(card)
    db.commit()
