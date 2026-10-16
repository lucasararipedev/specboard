"""Rotas pensadas para a IA: briefing, busca, backup, manual (/llms.txt) e prompt de conexão."""

from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..config import Settings
from ..deps import get_db, get_settings, project_or_404, require_token
from ..models import Activity, Card, Project, Question
from ..schemas import CardOut
from ..services.agent_docs import agent_guide, agent_prompt
from ..services.briefing import build_briefing, render_markdown
from ..services.serialize import activity_out, card_out, question_out

router = APIRouter(tags=["agent"], dependencies=[Depends(require_token)])
public = APIRouter(tags=["agent"])

MARKDOWN = "text/markdown; charset=utf-8"


def _briefing_response(briefing: dict, fmt: str):
    return briefing if fmt == "json" else PlainTextResponse(render_markdown(briefing), media_type=MARKDOWN)


@router.get("/api/briefing")
def briefing(
    format: Literal["md", "json"] = "md",
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Resumo de todos os projetos ativos, com lembretes para a IA puxar com o usuário."""
    return _briefing_response(build_briefing(db, settings), format)


@router.get("/api/projects/{slug}/briefing")
def project_briefing(
    slug: str,
    format: Literal["md", "json"] = "md",
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    project_or_404(db, slug)
    return _briefing_response(build_briefing(db, settings, slug=slug), format)


@router.get("/api/search", response_model=list[CardOut])
def search(
    q: str = Query(min_length=1),
    project: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Busca cards (sem diferenciar maiúsculas) para evitar duplicatas antes de criar."""
    term = f"%{q.lower()}%"
    query = select(Card).where(
        or_(
            func.lower(Card.title).like(term),
            func.lower(Card.description).like(term),
            func.lower(Card.spec_ref).like(term),
        )
    )
    if project:
        query = query.where(Card.project_id == project_or_404(db, project).id)
    query = query.order_by(Card.updated_at.desc()).limit(limit)
    return [card_out(settings, c) for c in db.scalars(query)]


@router.get("/api/export")
def export(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Backup completo em JSON (projetos com spec, cards, perguntas e atividades)."""
    projects = []
    for p in db.scalars(select(Project).order_by(Project.id)):
        cards = db.scalars(select(Card).where(Card.project_id == p.id).order_by(Card.id))
        questions = db.scalars(select(Question).where(Question.project_id == p.id).order_by(Question.id))
        activities = db.scalars(select(Activity).where(Activity.project_id == p.id).order_by(Activity.id))
        projects.append(
            {
                "slug": p.slug,
                "name": p.name,
                "summary": p.summary,
                "spec": p.spec,
                "repo": p.repo,
                "archived": p.archived,
                "created_at": p.created_at,
                "cards": [card_out(settings, c) for c in cards],
                "questions": [question_out(settings, q) for q in questions],
                "activity": [activity_out(a) for a in activities],
            }
        )
    return {"version": 1, "projects": projects}


@public.get("/llms.txt", response_class=PlainTextResponse)
@public.get("/api/agent/guide", response_class=PlainTextResponse)
def guide(settings: Settings = Depends(get_settings)):
    """Manual da API para agentes de IA, em Markdown."""
    return PlainTextResponse(agent_guide(settings), media_type=MARKDOWN)


@public.get("/api/agent/prompt", response_class=PlainTextResponse)
def prompt(settings: Settings = Depends(get_settings)):
    """Prompt para o usuário colar na IA dele (nunca inclui o token)."""
    return PlainTextResponse(agent_prompt(settings), media_type=MARKDOWN)
