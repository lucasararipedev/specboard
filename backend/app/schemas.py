"""Contratos da API. As descrições aparecem no /docs e ajudam a IA a usar os campos certos."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["backlog", "todo", "doing", "blocked", "done"]
QuestionStatus = Literal["open", "answered", "applied", "dismissed"]
Priority = int  # 0 (urgente) a 3 (algum dia)

SLUG_PATTERN = r"^[a-z0-9][a-z0-9-]{0,63}$"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(None, pattern=SLUG_PATTERN, description="Gerado a partir do nome se omitido")
    summary: str = Field("", description="Uma linha: o que é o projeto")
    spec: str = Field("", description="Spec em Markdown; fonte da verdade do projeto")
    repo: str = Field("", description="Caminho local ou URL do repositório")
    starter_questions: bool = Field(True, description="Cria as perguntas iniciais (problema, v1, prazo...)")


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    summary: str | None = None
    spec: str | None = None
    repo: str | None = None
    archived: bool | None = None


class ProjectOut(BaseModel):
    id: int
    slug: str
    name: str
    summary: str
    repo: str
    archived: bool
    url: str
    counts: dict[str, int]
    open_questions: int
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectOut):
    spec: str


class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field("", description="Markdown: contexto, critérios de aceite, links")
    status: Status = "backlog"
    priority: Priority = Field(2, ge=0, le=3, description="0 urgente, 1 alta, 2 normal, 3 algum dia")
    labels: list[str] = Field(default_factory=list)
    spec_ref: str = Field("", description='Seção da spec que o card implementa, ex.: "3.2 Login"')
    due_date: date | None = None


class CardUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = Field(None, ge=0, le=3)
    labels: list[str] | None = None
    spec_ref: str | None = None
    due_date: date | None = None
    position: float | None = Field(None, description="Ordem na coluna; omitido ao mudar de status = vai pro fim")


class CardOut(BaseModel):
    id: int
    project: str
    title: str
    description: str
    status: Status
    priority: int
    position: float
    labels: list[str]
    spec_ref: str
    due_date: date | None
    url: str
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    done_at: datetime | None


class QuestionCreate(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    context: str = Field("", description="Por que a resposta importa / o que muda com ela")
    options: list[str] = Field(default_factory=list, description="Respostas sugeridas (2 a 4 é o ideal)")
    card_id: int | None = None


class QuestionUpdate(BaseModel):
    answer: str | None = Field(None, description="Responder muda o status para answered")
    status: QuestionStatus | None = Field(None, description='A IA marca "applied" depois de usar a resposta')
    question: str | None = Field(None, min_length=1, max_length=1000)
    context: str | None = None
    options: list[str] | None = None


class QuestionOut(BaseModel):
    id: int
    project: str
    card_id: int | None
    question: str
    context: str
    options: list[str]
    answer: str
    status: QuestionStatus
    asked_by: str
    url: str
    created_at: datetime
    answered_at: datetime | None


class ActivityCreate(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    kind: Literal["note", "decision"] = "note"
    card_id: int | None = None


class ActivityOut(BaseModel):
    id: int
    project: str
    card_id: int | None
    actor: str
    kind: str
    message: str
    created_at: datetime
