from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import get_actor, get_db, project_or_404, require_token
from ..schemas import ActivityCreate, ActivityOut
from ..services import activity as service
from ..services.serialize import activity_out

router = APIRouter(prefix="/api/projects/{slug}/activity", tags=["activity"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[ActivityOut])
def list_activity(
    slug: str,
    limit: int = Query(50, ge=1, le=500),
    card_id: int | None = None,
    db: Session = Depends(get_db),
):
    return [activity_out(a) for a in service.list_activity(db, project_or_404(db, slug), limit, card_id)]


@router.post("", response_model=ActivityOut, status_code=201)
def log_activity(
    slug: str,
    body: ActivityCreate,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor),
):
    """Registra o que foi feito ("note") ou decidido ("decision"), opcionalmente ligado a um card."""
    return activity_out(service.log_activity(db, project_or_404(db, slug), body, actor))
