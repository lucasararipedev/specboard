"""Dependências compartilhadas pelas rotas: sessão do banco, settings, token e autor."""

import secrets
from collections.abc import Iterator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .models import Card, Project


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.sessionmaker() as db:
        yield db


def require_token(
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(None),
) -> None:
    if not settings.api_token:
        return
    given = (authorization or "").removeprefix("Bearer ").strip()
    if not secrets.compare_digest(given, settings.api_token):
        raise HTTPException(401, "Token inválido ou ausente (Authorization: Bearer <SPECBOARD_TOKEN>)")


def get_actor(x_actor: str | None = Header(None)) -> str:
    """A IA se identifica com o header X-Actor (ex.: "claude"); a interface manda "user"."""
    return (x_actor or "user").strip()[:64] or "user"


def project_or_404(db: Session, slug: str) -> Project:
    project = db.scalar(select(Project).where(Project.slug == slug))
    if project is None:
        raise HTTPException(404, f"Projeto '{slug}' não existe. Liste com GET /api/projects")
    return project


def card_or_404(db: Session, card_id: int) -> Card:
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(404, f"Card #{card_id} não existe")
    return card
