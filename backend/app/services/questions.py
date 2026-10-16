"""Perguntas iniciais de todo projeto novo: o mínimo que a IA precisa saber para não ficar supondo."""

from sqlalchemy.orm import Session

from ..models import Question

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
