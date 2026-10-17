from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..config import Settings
from ..deps import get_actor, get_db, get_settings, project_or_404, require_token
from ..schemas import CardCreate, CardOut, CardUpdate, Status
from ..services import cards as service
from ..services.serialize import card_out

router = APIRouter(prefix="/api", tags=["cards"], dependencies=[Depends(require_token)])


@router.get("/projects/{slug}/cards", response_model=list[CardOut])
def list_cards(
    slug: str,
    status: Status | None = None,
    label: list[str] = Query([], description="Só cards com todas estas etiquetas (repita: ?label=v0.2&label=front)"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Cards do projeto. `?label=v0.2` traz só os que têm a etiqueta; repetir o parâmetro exige todas."""
    project = project_or_404(db, slug)
    return [card_out(settings, c) for c in service.list_cards(db, project, status, label)]


@router.post("/projects/{slug}/cards", response_model=CardOut, status_code=201)
def create_card(
    slug: str,
    body: CardCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    return card_out(settings, service.create_card(db, project_or_404(db, slug), body, actor))


@router.get("/cards/{card_id}", response_model=CardOut)
def get_card(card_id: int, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return card_out(settings, service.get_card(db, card_id))


@router.patch("/cards/{card_id}", response_model=CardOut)
def update_card(
    card_id: int,
    body: CardUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    """Edita qualquer campo. Mudar o status registra uma atividade automaticamente."""
    return card_out(settings, service.update_card(db, service.get_card(db, card_id), body, actor))


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: int, db: Session = Depends(get_db), actor: str = Depends(get_actor)):
    service.delete_card(db, service.get_card(db, card_id), actor)
