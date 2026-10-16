"""Briefing: o resumo que a IA lê no começo de cada sessão para lembrar o usuário das prioridades.

Além dos cards, gera "lembretes" (nudges): instruções curtas do que a IA deve puxar com o usuário,
como card parado, WIP alto, P0 esquecido no backlog ou projeto sem spec.
"""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import PRIORITY_LABELS, Activity, Card, Project
from .serialize import card_url, project_url, status_counts

NEXT_UP_LIMIT = 5
WIP_LIMIT = 3
QUIET_DAYS = 7


def _brief(settings: Settings, slug: str, card: Card) -> dict:
    return {
        "id": card.id,
        "title": card.title,
        "status": card.status,
        "priority": card.priority,
        "spec_ref": card.spec_ref,
        "due_date": card.due_date.isoformat() if card.due_date else None,
        "updated_at": card.updated_at.isoformat(),
        "url": card_url(settings, slug, card.id),
    }


def _project_briefing(db: Session, settings: Settings, project: Project, now: datetime, today: date) -> dict:
    cards = list(db.scalars(select(Card).where(Card.project_id == project.id)))
    by_rank = sorted(cards, key=lambda c: (c.priority, c.position))

    doing = [c for c in by_rank if c.status == "doing"]
    blocked = [c for c in by_rank if c.status == "blocked"]
    next_up = [c for c in by_rank if c.status == "todo"][:NEXT_UP_LIMIT]
    urgent_backlog = [c for c in by_rank if c.status == "backlog" and c.priority <= 1]
    overdue = [c for c in by_rank if c.due_date and c.due_date < today and c.status != "done"]
    stale_cutoff = now - timedelta(days=settings.stale_days)
    stale = [c for c in doing + blocked if c.updated_at < stale_cutoff]
    week_ago = now - timedelta(days=7)
    done_last_7_days = sum(1 for c in cards if c.done_at and c.done_at >= week_ago)

    last = db.scalar(
        select(Activity)
        .where(Activity.project_id == project.id)
        .order_by(Activity.created_at.desc(), Activity.id.desc())
        .limit(1)
    )

    nudges: list[str] = []
    if not project.spec.strip():
        nudges.append("Projeto sem spec: proponha escrever uma (objetivo, público, escopo da v1, fora de escopo).")
    if not doing and next_up:
        nudges.append(f'Nada em andamento: sugira começar #{next_up[0].id} "{next_up[0].title}".')
    if not doing and not next_up and not urgent_backlog and cards:
        nudges.append("Fila do todo vazia: ajude o usuário a priorizar o backlog.")
    if len(doing) > WIP_LIMIT:
        nudges.append(f"{len(doing)} cards em andamento: sugira terminar algum antes de puxar mais.")
    for c in stale:
        days = (now - c.updated_at).days
        nudges.append(f'#{c.id} "{c.title}" está em {c.status} sem atualização há {days} dias: pergunte como está.')
    for c in overdue:
        nudges.append(f'#{c.id} "{c.title}" venceu em {c.due_date.isoformat()}.')
    for c in urgent_backlog:
        nudges.append(f'#{c.id} "{c.title}" é {PRIORITY_LABELS[c.priority]} e está no backlog: sugira mover pro todo.')
    if last and last.created_at < now - timedelta(days=QUIET_DAYS):
        nudges.append(f"Sem atividade há {(now - last.created_at).days} dias: pergunte se o projeto segue ativo.")

    return {
        "slug": project.slug,
        "name": project.name,
        "summary": project.summary,
        "repo": project.repo,
        "url": project_url(settings, project.slug),
        "has_spec": bool(project.spec.strip()),
        "counts": status_counts(db, project.id),
        "doing": [_brief(settings, project.slug, c) for c in doing],
        "blocked": [_brief(settings, project.slug, c) for c in blocked],
        "next_up": [_brief(settings, project.slug, c) for c in next_up],
        "overdue": [_brief(settings, project.slug, c) for c in overdue],
        "done_last_7_days": done_last_7_days,
        "last_activity": (
            {"at": last.created_at.isoformat(), "actor": last.actor, "message": last.message} if last else None
        ),
        "nudges": nudges,
    }


def build_briefing(db: Session, settings: Settings, slug: str | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    query = select(Project).where(Project.archived.is_(False)).order_by(Project.updated_at.desc())
    if slug:
        query = select(Project).where(Project.slug == slug)
    projects = [_project_briefing(db, settings, p, now, now.date()) for p in db.scalars(query)]
    return {"generated_at": now.isoformat(), "board_url": settings.public_url, "projects": projects}


def _line(card: dict) -> str:
    extra = []
    if card["spec_ref"]:
        extra.append(f"spec {card['spec_ref']}")
    if card["due_date"]:
        extra.append(f"prazo {card['due_date']}")
    suffix = f" ({', '.join(extra)})" if extra else ""
    return f"- #{card['id']} [{PRIORITY_LABELS[card['priority']]}] {card['title']}{suffix} — {card['url']}"


def render_markdown(briefing: dict) -> str:
    out = [f"# Briefing do Specboard — {briefing['generated_at'][:16].replace('T', ' ')} UTC", ""]
    out.append(f"Board: {briefing['board_url']}")
    if not briefing["projects"]:
        out += ["", "Nenhum projeto ainda. Pergunte ao usuário em que ele está trabalhando e crie o primeiro."]
        return "\n".join(out) + "\n"

    for p in briefing["projects"]:
        counts = p["counts"]
        out += ["", f"## {p['name']} (`{p['slug']}`) — {p['url']}"]
        if p["summary"]:
            out.append(p["summary"])
        out.append(
            f"backlog {counts['backlog']} · todo {counts['todo']} · doing {counts['doing']} · "
            f"blocked {counts['blocked']} · done {counts['done']} ({p['done_last_7_days']} nos últimos 7 dias)"
        )
        for title, key in (("Em andamento", "doing"), ("Travado", "blocked"), ("Próximos", "next_up")):
            if p[key]:
                out += ["", f"**{title}**"] + [_line(c) for c in p[key]]
        if p["last_activity"]:
            a = p["last_activity"]
            out += ["", f"Última atividade: {a['at'][:10]} ({a['actor']}) {a['message']}"]
        if p["nudges"]:
            out += ["", "**Lembretes para puxar com o usuário**"] + [f"- {n}" for n in p["nudges"]]
    return "\n".join(out) + "\n"
