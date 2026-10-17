"""Sessões: chats ou agentes ligados ao board ("/board"). Alimentam o painel Agora e o briefing.

O plugin do Claude Code manda o JSON cru dos hooks para /api/hooks/claude-code (só precisa de curl);
as demais IAs ligam a sessão pelo MCP ou pela API.
"""

import secrets
from datetime import timedelta
from pathlib import PurePosixPath

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..db import utcnow
from ..models import AgentSession, Card, Project
from .briefing import build_briefing, render_markdown
from .serialize import project_url

# Sessões encerradas há mais que isso são apagadas (o histórico de verdade fica nas atividades).
KEEP_ENDED = timedelta(days=30)


def _norm(path: str) -> str:
    return path.strip().replace("\\", "/").rstrip("/")


def _repo_name(repo: str) -> str:
    """Último pedaço do caminho ou da URL do repositório, sem .git."""
    name = _norm(repo).rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    return name.removesuffix(".git").lower()


def match_project(db: Session, cwd: str) -> Project | None:
    """Acha o projeto da pasta: repo igual ou pasta-mãe (o mais específico ganha), com "~/" valendo como
    sufixo. Sem isso, o nome da pasta igual ao slug ou ao nome do repo, se só um projeto bater."""
    cwd = _norm(cwd)
    if not cwd:
        return None
    projects = list(db.scalars(select(Project).where(Project.archived.is_(False))))

    best, best_len = None, -1
    for p in projects:
        repo = _norm(p.repo)
        if not repo or "://" in repo or repo.startswith("git@"):
            continue
        if repo.startswith("~/"):
            tail = repo[1:]
            hit = cwd.endswith(tail) or f"{tail}/" in cwd
        else:
            hit = cwd == repo or cwd.startswith(f"{repo}/")
        if hit and len(repo) > best_len:
            best, best_len = p, len(repo)
    if best:
        return best

    folder = PurePosixPath(cwd).name.lower()
    by_name = [p for p in projects if folder in (p.slug, _repo_name(p.repo))]
    return by_name[0] if len(by_name) == 1 else None


def get_session(db: Session, key: str) -> AgentSession:
    session = db.scalar(select(AgentSession).where(AgentSession.key == key))
    if session is None:
        raise HTTPException(404, f"Sessão '{key}' não existe. Ligue com POST /api/sessions")
    return session


def list_sessions(db: Session, active_only: bool = True, project: Project | None = None) -> list[AgentSession]:
    query = select(AgentSession).order_by(AgentSession.last_seen_at.desc())
    if active_only:
        query = query.where(AgentSession.active.is_(True), AgentSession.ended_at.is_(None))
    if project:
        query = query.where(AgentSession.project_id == project.id)
    return list(db.scalars(query))


def _project_by_slug(db: Session, slug: str) -> Project:
    project = db.scalar(select(Project).where(Project.slug == slug))
    if project is None:
        raise HTTPException(404, f"Projeto '{slug}' não existe. Liste com GET /api/projects")
    return project


def _check_card(db: Session, card_id: int | None) -> None:
    if card_id is not None and db.get(Card, card_id) is None:
        raise HTTPException(404, f"Card #{card_id} não existe")


def upsert_session(
    db: Session,
    *,
    actor: str,
    key: str | None = None,
    client: str | None = None,
    project: str | None = None,
    cwd: str | None = None,
    doing: str | None = None,
    card_id: int | None = None,
    active: bool | None = True,
) -> AgentSession:
    """Liga (ou atualiza) a sessão. Sem key, gera uma; sem projeto, tenta achar pela pasta."""
    session = db.scalar(select(AgentSession).where(AgentSession.key == key)) if key else None
    if session is None:
        session = AgentSession(key=key or secrets.token_hex(8), actor=actor, client=client or "", cwd="", doing="")
        db.add(session)
    if client:
        session.client = client
    if cwd is not None:
        session.cwd = cwd[:500]
    if project:
        session.project = _project_by_slug(db, project)
    elif session.project_id is None and session.cwd:
        session.project = match_project(db, session.cwd)
    if doing is not None:
        session.doing = doing[:300]
    if card_id is not None:
        _check_card(db, card_id)
        session.card_id = card_id
    if active is not None:
        session.active = active
    session.actor = actor or session.actor
    session.ended_at = None
    session.last_seen_at = utcnow()
    db.commit()
    return session


def update_session(
    db: Session, session: AgentSession, *, project: str | None, doing: str | None, card_id: int | None, active: bool | None
) -> AgentSession:
    if project:
        session.project = _project_by_slug(db, project)
    if doing is not None:
        session.doing = doing[:300]
    if card_id is not None:
        _check_card(db, card_id)
        session.card_id = card_id
    if active is not None:
        session.active = active
    session.last_seen_at = utcnow()
    db.commit()
    return session


def end_session(db: Session, session: AgentSession) -> AgentSession:
    session.active = False
    session.ended_at = utcnow()
    db.commit()
    return session


def status_line(settings: Settings, session: AgentSession) -> str:
    if not session.active:
        return "Specboard desligado neste chat. Use /board para ligar."
    if session.project:
        return f"Specboard ativo neste chat · projeto {session.project.slug} · {project_url(settings, session.project.slug)}"
    return f"Specboard ativo neste chat · sem projeto definido · {settings.public_url}/projetos"


def _context(db: Session, settings: Settings, session: AgentSession) -> str:
    """O que o hook injeta no contexto da IA no começo do chat."""
    if not session.active:
        return (
            f'Specboard disponível ({settings.public_url}), desligado neste chat (sessão "{session.key}"). '
            'Se o usuário rodar /board ou pedir para ligar, use a tool `session` do MCP specboard com '
            f'action "on" e session "{session.key}".'
        )
    lines = [
        f'Specboard ligado neste chat: sessão "{session.key}"'
        + (f', projeto "{session.project.slug}".' if session.project else ", sem projeto definido."),
        "Mantenha o board em dia pelas tools do MCP specboard, sem o usuário pedir: cards para tarefas, ideias e "
        "bugs; status conforme o trabalho anda; decisões na spec; perguntas quando faltar contexto.",
        f'Ao começar uma tarefa, atualize o "fazendo agora" com a tool `session` (action "doing", session '
        f'"{session.key}"). Ao terminar, use /board para sincronizar o que faltou.',
    ]
    if session.project:
        lines += ["", render_markdown(build_briefing(db, settings, slug=session.project.slug)).strip()]
    return "\n".join(lines)


def handle_claude_code_hook(db: Session, settings: Settings, payload: dict) -> dict:
    """Responde aos hooks SessionStart, Stop e SessionEnd do plugin. Nunca falha: evento estranho dá {}."""
    event = payload.get("hook_event_name")
    key = str(payload.get("session_id") or "")[:128]
    if not key:
        return {}
    session = db.scalar(select(AgentSession).where(AgentSession.key == key))

    if event == "SessionStart":
        db.execute(delete(AgentSession).where(AgentSession.ended_at < utcnow() - KEEP_ENDED))
        if session is None:
            cwd = str(payload.get("cwd") or "")
            project = match_project(db, cwd)
            # Liga sozinho quando a pasta é de um projeto do board; nas outras, espera o /board.
            session = upsert_session(
                db, actor="claude", key=key, client="claude-code", cwd=cwd, active=project is not None
            )
        else:
            session.ended_at = None
            session.last_seen_at = utcnow()
            db.commit()
        out: dict = {
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": _context(db, settings, session)}
        }
        if session.active:
            out["systemMessage"] = status_line(settings, session)
        return out

    if session is None:
        return {}
    if event == "Stop" and session.active:
        session.last_seen_at = utcnow()
        db.commit()
    elif event == "SessionEnd":
        end_session(db, session)
    return {}
