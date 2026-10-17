"""Modelo de dados: Project (com a spec) → Card (o kanban), Question (o que a IA precisa saber), Activity (o diário),
AgentSession (chats ligados ao board) e Profile (o usuário).

O esquema muda só por migração do Alembic (app/migrations). Mudou um modelo? Crie uma migração nova.
"""

from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, UTCDateTime, utcnow

# Ordem das colunas no board.
STATUSES = ("backlog", "todo", "doing", "blocked", "done")

# 0 = urgente, 3 = algum dia.
PRIORITY_LABELS = {0: "P0", 1: "P1", 2: "P2", 3: "P3"}

# open: esperando o usuário · answered: respondida, a IA ainda não usou · applied: a IA já incorporou
# na spec/cards · dismissed: o usuário dispensou.
QUESTION_STATUSES = ("open", "answered", "applied", "dismissed")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text, default="")
    # Fonte da verdade do projeto, em Markdown. Cards apontam para seções dela (spec_ref).
    spec: Mapped[str] = mapped_column(Text, default="")
    # Caminho local ou URL do repositório; ajuda a IA a achar o projeto certo.
    repo: Mapped[str] = mapped_column(String(500), default="")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    cards: Mapped[list["Card"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", passive_deletes=True
    )


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="backlog", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=2)
    # Ordem dentro da coluna (menor fica em cima). Float para inserir entre dois cards sem renumerar.
    position: Mapped[float] = mapped_column(default=0.0)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list)
    spec_ref: Mapped[str] = mapped_column(String(200), default="")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    done_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    project: Mapped[Project] = relationship(back_populates="cards")


class Question(Base):
    """Pergunta para o usuário responder. Quanto mais respondidas, menos a IA precisa supor."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id", ondelete="SET NULL"), nullable=True)
    question: Mapped[str] = mapped_column(Text)
    # Por que a resposta importa / o que muda com ela.
    context: Mapped[str] = mapped_column(Text, default="")
    # Respostas sugeridas; o usuário clica numa ou escreve a própria.
    options: Mapped[list[str]] = mapped_column(JSON, default=list)
    answer: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="open", index=True)
    asked_by: Mapped[str] = mapped_column(String(64), default="user")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    answered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    project: Mapped[Project] = relationship(back_populates="questions")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id", ondelete="SET NULL"), nullable=True)
    # Quem fez: "user" (interface) ou o nome que a IA manda no header X-Actor ("claude", "chatgpt"...).
    actor: Mapped[str] = mapped_column(String(64), default="user")
    # created | status | spec | deleted | note | decision
    kind: Mapped[str] = mapped_column(String(32), default="note")
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

    project: Mapped[Project] = relationship(back_populates="activities")


class AgentSession(Base):
    """Um chat ou agente ligado ao board ("/board"). Alimenta o painel Agora."""

    __tablename__ = "agent_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    # session_id do Claude Code, ou um id gerado quando a IA liga a sessão sem ter um.
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    actor: Mapped[str] = mapped_column(String(64), default="ia")
    # De onde vem: "claude-code", "mcp"...
    client: Mapped[str] = mapped_column(String(64), default="")
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    cwd: Mapped[str] = mapped_column(String(500), default="")
    # O que o agente está fazendo agora, em uma linha.
    doing: Mapped[str] = mapped_column(String(300), default="")
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id", ondelete="SET NULL"), nullable=True)
    # Ligada: aparece no painel e recebe os lembretes. Desligada: o chat segue sem o Specboard.
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    project: Mapped[Project | None] = relationship()
    card: Mapped[Card | None] = relationship()


class Profile(Base):
    """O usuário desta instância (uma linha só): nome e foto opcional, só na máquina dele."""

    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), default="")
    # Foto pequena como data URL (image/png, jpeg ou webp).
    avatar: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
