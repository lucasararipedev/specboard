"""Perguntas para o usuário: a IA pergunta quando falta contexto, o usuário responde na interface e a
IA incorpora a resposta (status applied) na spec ou nos cards."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..db import utcnow
from ..deps import get_actor, get_db, get_settings, project_or_404, require_token
from ..models import Activity, Card, Question
from ..schemas import QuestionCreate, QuestionOut, QuestionStatus, QuestionUpdate
from ..services.serialize import question_out

router = APIRouter(prefix="/api", tags=["questions"], dependencies=[Depends(require_token)])


def question_or_404(db: Session, question_id: int) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(404, f"Pergunta {question_id} não existe")
    return question


def short(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


@router.get("/projects/{slug}/questions", response_model=list[QuestionOut])
def list_questions(
    slug: str,
    status: QuestionStatus | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    project = project_or_404(db, slug)
    query = select(Question).where(Question.project_id == project.id).order_by(Question.id)
    if status:
        query = query.where(Question.status == status)
    return [question_out(settings, q) for q in db.scalars(query)]


@router.post("/projects/{slug}/questions", response_model=QuestionOut, status_code=201)
def ask(
    slug: str,
    body: QuestionCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    """Registra uma pergunta para o usuário. Prefira perguntas objetivas, com 2 a 4 opções."""
    project = project_or_404(db, slug)
    if body.card_id is not None:
        card = db.get(Card, body.card_id)
        if card is None or card.project_id != project.id:
            raise HTTPException(404, f"Card #{body.card_id} não existe neste projeto")
    question = Question(project_id=project.id, asked_by=actor, **body.model_dump())
    db.add(question)
    db.flush()
    db.add(
        Activity(
            project_id=project.id,
            card_id=body.card_id,
            actor=actor,
            kind="question",
            message=f"Perguntou: {short(question.question)}",
        )
    )
    project.updated_at = utcnow()
    db.commit()
    return question_out(settings, question)


@router.patch("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    body: QuestionUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    """Responder (answer) muda o status para answered. A IA marca applied depois de usar a resposta."""
    question = question_or_404(db, question_id)
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    new_status = changes.pop("status", None)
    answer = changes.pop("answer", None)

    for field, value in changes.items():
        setattr(question, field, value)

    if answer is not None:
        question.answer = answer.strip()
        if question.answer:
            question.answered_at = utcnow()
            question.status = "answered"
            db.add(
                Activity(
                    project_id=question.project_id,
                    card_id=question.card_id,
                    actor=actor,
                    kind="answer",
                    message=f"Respondeu: {short(question.question, 80)} → {short(question.answer)}",
                )
            )
        else:
            question.answered_at = None
            question.status = "open"

    if new_status:
        if new_status in ("answered", "applied") and not question.answer:
            raise HTTPException(422, "A pergunta ainda não tem resposta")
        question.status = new_status

    question.project.updated_at = utcnow()
    db.commit()
    return question_out(settings, question)


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    db.delete(question_or_404(db, question_id))
    db.commit()
