"""Perguntas para o usuário: a IA pergunta quando falta contexto, o usuário responde na interface e a
IA incorpora a resposta (status applied) na spec ou nos cards."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import Settings
from ..deps import get_actor, get_db, get_settings, project_or_404, require_token
from ..schemas import QuestionCreate, QuestionOut, QuestionStatus, QuestionUpdate
from ..services import questions as service
from ..services.serialize import question_out

router = APIRouter(prefix="/api", tags=["questions"], dependencies=[Depends(require_token)])


@router.get("/projects/{slug}/questions", response_model=list[QuestionOut])
def list_questions(
    slug: str,
    status: QuestionStatus | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return [question_out(settings, q) for q in service.list_questions(db, project_or_404(db, slug), status)]


@router.post("/projects/{slug}/questions", response_model=QuestionOut, status_code=201)
def ask(
    slug: str,
    body: QuestionCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    """Registra uma pergunta para o usuário. Prefira perguntas objetivas, com 2 a 4 opções."""
    return question_out(settings, service.ask_question(db, project_or_404(db, slug), body, actor))


@router.patch("/questions/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    body: QuestionUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    """Responder (answer) muda o status para answered. A IA marca applied depois de usar a resposta."""
    return question_out(settings, service.update_question(db, service.get_question(db, question_id), body, actor))


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    db.delete(service.get_question(db, question_id))
    db.commit()
