"""Perguntas para o usuário: as iniciais de todo projeto novo e as regras de perguntar e responder."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import utcnow
from ..models import Activity, Card, Project, Question
from ..schemas import QuestionCreate, QuestionUpdate

STARTER_QUESTIONS = [
    {
        "question": "Qual problema este projeto resolve, e para quem?",
        "context": "Guia a spec e o que vem primeiro.",
        "options": [],
    },
    {
        "question": "O que precisa estar pronto para você considerar a v1 entregue?",
        "context": "Vira o escopo da v1 na spec e os primeiros cards.",
        "options": [],
    },
    {
        "question": "Tem prazo ou alguma data importante?",
        "context": "Define prioridades e prazos dos cards.",
        "options": ["Sem prazo", "Este mês", "Nos próximos 3 meses"],
    },
    {
        "question": "O que fica de fora por enquanto?",
        "context": "Evita que a IA sugira coisa fora do escopo.",
        "options": [],
    },
    {
        "question": "Quanto tempo por semana você consegue dedicar a ele?",
        "context": "Ajuda a dimensionar o que cabe em cada semana.",
        "options": ["Menos de 5 h", "De 5 a 15 h", "Tempo integral"],
    },
]


def add_starter_questions(db: Session, project_id: int) -> None:
    for q in STARTER_QUESTIONS:
        db.add(Question(project_id=project_id, asked_by="specboard", **q))


def short(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def get_question(db: Session, question_id: int) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(404, f"Pergunta {question_id} não existe")
    return question


def list_questions(db: Session, project: Project, status: str | None = None) -> list[Question]:
    query = select(Question).where(Question.project_id == project.id).order_by(Question.id)
    if status:
        query = query.where(Question.status == status)
    return list(db.scalars(query))


def ask_question(db: Session, project: Project, body: QuestionCreate, actor: str) -> Question:
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
    return question


def update_question(db: Session, question: Question, body: QuestionUpdate, actor: str) -> Question:
    """Responder (answer) muda o status para answered. A IA marca applied depois de usar a resposta."""
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
    return question
