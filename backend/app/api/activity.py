from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import utcnow
from ..deps import get_actor, get_db, project_or_404, require_token
from ..models import Activity, Card
from ..schemas import ActivityCreate, ActivityOut
from ..services.serialize import activity_out

router = APIRouter(prefix="/api/projects/{slug}/activity", tags=["activity"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[ActivityOut])
def list_activity(
    slug: str,
    limit: int = Query(50, ge=1, le=500),
    card_id: int | None = None,
    db: Session = Depends(get_db),
):
    project = project_or_404(db, slug)
    query = select(Activity).where(Activity.project_id == project.id)
    if card_id is not None:
        query = query.where(Activity.card_id == card_id)
    query = query.order_by(Activity.created_at.desc(), Activity.id.desc()).limit(limit)
    return [activity_out(a) for a in db.scalars(query)]


@router.post("", response_model=ActivityOut, status_code=201)
def log_activity(
    slug: str,
    body: ActivityCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
):
    """Registra o que foi feito ("note") ou decidido ("decision"), opcionalmente ligado a um card."""
    project = project_or_404(db, slug)
    if body.card_id is not None:
        card = db.get(Card, body.card_id)
        if card is None or card.project_id != project.id:
            raise HTTPException(404, f"Card #{body.card_id} não existe neste projeto")
    activity = Activity(project_id=project.id, actor=actor, **body.model_dump())
    db.add(activity)
    project.updated_at = utcnow()
    db.commit()
    return activity_out(activity)
