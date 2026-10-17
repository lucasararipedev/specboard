"""Sessões (chats ligados ao board) e o endpoint dos hooks do plugin do Claude Code."""

import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..config import Settings
from ..deps import get_actor, get_db, get_settings, project_or_404, require_token
from ..schemas import SessionOut, SessionUpdate, SessionUpsert
from ..services import sessions as service
from ..services.serialize import session_out

router = APIRouter(prefix="/api", tags=["sessions"], dependencies=[Depends(require_token)])


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(
    active: bool = True,
    project: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Painel Agora: quem está ligado e o que está fazendo. `idle` = sem sinal há mais de 15 min."""
    target = project_or_404(db, project) if project else None
    return [session_out(settings, s) for s in service.list_sessions(db, active, target)]


@router.post("/sessions", response_model=SessionOut)
def upsert_session(
    body: SessionUpsert,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    """Liga o chat ao board (ou atualiza). Sem `key`, gera uma: guarde e reuse nas próximas chamadas."""
    session = service.upsert_session(db, actor=actor, **body.model_dump())
    return session_out(settings, session)


@router.patch("/sessions/{key}", response_model=SessionOut)
def update_session(
    key: str, body: SessionUpdate, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
):
    """Atualiza o "fazendo agora" (`doing`, `card_id`) e serve de sinal de vida."""
    session = service.update_session(db, service.get_session(db, key), **body.model_dump())
    return session_out(settings, session)


@router.delete("/sessions/{key}", response_model=SessionOut)
def end_session(key: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Desliga o chat: sai do painel Agora."""
    return session_out(settings, service.end_session(db, service.get_session(db, key)))


@router.post("/hooks/claude-code", include_in_schema=False)
async def claude_code_hook(request: Request, settings: Settings = Depends(get_settings)):
    """Recebe o JSON cru dos hooks do plugin (SessionStart, Stop, SessionEnd) e devolve a saída do hook."""
    try:
        payload = json.loads(await request.body() or b"{}")
    except ValueError:
        return {}
    if not isinstance(payload, dict):
        return {}
    with request.app.state.sessionmaker() as db:
        return service.handle_claude_code_hook(db, settings, payload)
