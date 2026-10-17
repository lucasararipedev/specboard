"""Servidor MCP em /mcp (Streamable HTTP): as mesmas regras da API, como tools para a IA.

As tools chamam os mesmos serviços das rotas REST, então atividade automática, versões e `url` funcionam igual.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from typing import Any, Literal

from fastapi import HTTPException
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker
from starlette.routing import BaseRoute

from .config import Settings
from .deps import project_or_404
from .schemas import (
    ActivityCreate,
    CardCreate,
    CardUpdate,
    ProjectCreate,
    ProjectUpdate,
    QuestionCreate,
    QuestionUpdate,
)
from .services import activity, cards, projects, questions, sessions
from .services.agent_docs import board_prompt, mcp_instructions
from .services.briefing import build_briefing, render_markdown
from .services.serialize import (
    activity_out,
    card_out,
    project_out,
    question_out,
    session_out,
)

Status = Literal["backlog", "todo", "doing", "blocked", "done"]


def _dump(model) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _given(**fields) -> dict[str, Any]:
    """Só os campos que a IA mandou (None = não mexer)."""
    return {k: v for k, v in fields.items() if v is not None}


def build_mcp(settings: Settings, make_session: sessionmaker) -> MCPServer:
    mcp = MCPServer(name="specboard", title="Specboard", instructions=mcp_instructions(settings))

    @contextmanager
    def db_for() -> Iterator[Session]:
        with make_session() as db:
            try:
                yield db
            except HTTPException as e:
                raise ToolError(str(e.detail)) from None
            except ValidationError as e:
                raise ToolError(f"Campos inválidos: {e.errors(include_url=False)}") from None
            except ValueError as e:
                raise ToolError(f"Valor inválido: {e}") from None

    def actor(ctx: Context) -> str:
        """X-Actor da configuração do cliente; senão, o nome que o cliente MCP informa."""
        header = (ctx.headers or {}).get("x-actor", "").strip()
        if header:
            return header[:64]
        params = getattr(ctx.session, "client_params", None)
        name = getattr(getattr(params, "client_info", None), "name", "") or "ia"
        return name.strip()[:64] or "ia"

    @mcp.tool()
    def briefing(project: str | None = None) -> str:
        """Resumo do board com lembretes para puxar com o usuário. Rode no começo de cada sessão."""
        with db_for() as db:
            if project:
                project_or_404(db, project)
            return render_markdown(build_briefing(db, settings, slug=project))

    @mcp.tool()
    def list_projects(include_archived: bool = False) -> list[dict]:
        """Projetos com contagens. Compare `repo` e `slug` com a pasta atual para achar o projeto certo."""
        with db_for() as db:
            return [_dump(project_out(db, settings, p)) for p in projects.list_projects(db, include_archived)]

    @mcp.tool()
    def get_project(project: str) -> dict:
        """Projeto com a spec (fonte da verdade do planejamento) e as etiquetas em uso (`labels`, com contagem).
        Leia antes de planejar e reaproveite as etiquetas existentes."""
        with db_for() as db:
            return _dump(project_out(db, settings, project_or_404(db, project), detail=True))

    @mcp.tool()
    def save_project(
        ctx: Context,
        project: str | None = None,
        name: str | None = None,
        summary: str | None = None,
        spec: str | None = None,
        repo: str | None = None,
        archived: bool | None = None,
    ) -> dict:
        """Sem `project`, cria um projeto (precisa de `name`; `repo` = pasta ou URL do repositório). Com
        `project` (slug), edita. A `spec` vai sempre inteira, em Markdown."""
        with db_for() as db:
            if project:
                body = ProjectUpdate(**_given(name=name, summary=summary, spec=spec, repo=repo, archived=archived))
                saved = projects.update_project(db, project_or_404(db, project), body, actor(ctx))
            else:
                if not name:
                    raise ToolError("Para criar um projeto, informe `name`")
                body = ProjectCreate(**_given(name=name, summary=summary, spec=spec, repo=repo))
                saved = projects.create_project(db, body, actor(ctx))
            return _dump(project_out(db, settings, saved, detail=True))

    @mcp.tool()
    def search_cards(
        query: str, project: str | None = None, labels: list[str] | None = None, limit: int = 20
    ) -> list[dict]:
        """Busca cards por título, descrição e spec_ref. Use antes de criar, para não duplicar."""
        with db_for() as db:
            target = project_or_404(db, project) if project else None
            found = cards.search_cards(db, query, target, labels, max(1, min(limit, 100)))
            return [_dump(card_out(settings, c)) for c in found]

    @mcp.tool()
    def list_cards(project: str, status: Status | None = None, labels: list[str] | None = None) -> list[dict]:
        """Cards do projeto. `labels` traz só os que têm todas essas etiquetas (ex.: ["v0.2"] = entregas da v0.2)."""
        with db_for() as db:
            found = cards.list_cards(db, project_or_404(db, project), status, labels)
            return [_dump(card_out(settings, c)) for c in found]

    @mcp.tool()
    def save_card(
        ctx: Context,
        project: str | None = None,
        card_id: int | None = None,
        title: str | None = None,
        description: str | None = None,
        status: Status | None = None,
        priority: int | None = None,
        labels: list[str] | None = None,
        spec_ref: str | None = None,
        due_date: str | None = None,
    ) -> dict:
        """Sem `card_id`, cria um card em `project` (precisa de `title`). Com `card_id`, edita só os campos
        enviados. `status`: backlog, todo, doing, blocked, done. `priority`: 0 urgente a 3 algum dia.
        `labels`: lista completa de etiquetas (tipo, área ou versão, ex.: ["bug", "v0.2"]); reaproveite as do
        projeto. `due_date`: AAAA-MM-DD ("" limpa)."""
        with db_for() as db:
            fields = _given(
                title=title,
                description=description,
                status=status,
                priority=priority,
                labels=labels,
                spec_ref=spec_ref,
            )
            if due_date is not None:
                fields["due_date"] = date.fromisoformat(due_date) if due_date else None
            if card_id is not None:
                saved = cards.update_card(db, cards.get_card(db, card_id), CardUpdate(**fields), actor(ctx))
            else:
                if not project or not title:
                    raise ToolError("Para criar um card, informe `project` e `title`")
                saved = cards.create_card(db, project_or_404(db, project), CardCreate(**fields), actor(ctx))
            return _dump(card_out(settings, saved))

    @mcp.tool()
    def log_activity(
        ctx: Context, project: str, message: str, kind: Literal["note", "decision"] = "note", card_id: int | None = None
    ) -> dict:
        """Registra o que foi feito (`note`) ou decidido (`decision`), ligado ou não a um card."""
        with db_for() as db:
            body = ActivityCreate(message=message, kind=kind, card_id=card_id)
            return _dump(activity_out(activity.log_activity(db, project_or_404(db, project), body, actor(ctx))))

    @mcp.tool()
    def save_question(
        ctx: Context,
        project: str | None = None,
        question_id: int | None = None,
        question: str | None = None,
        context: str | None = None,
        options: list[str] | None = None,
        card_id: int | None = None,
        answer: str | None = None,
        status: Literal["open", "answered", "applied", "dismissed"] | None = None,
    ) -> dict:
        """Sem `question_id`, pergunta ao usuário em `project` (objetiva, com 2 a 4 `options`). Com
        `question_id`, registra a resposta (`answer`) ou marca `status: "applied"` depois de usar a resposta."""
        with db_for() as db:
            if question_id is not None:
                body = QuestionUpdate(**_given(question=question, context=context, options=options, answer=answer, status=status))
                saved = questions.update_question(db, questions.get_question(db, question_id), body, actor(ctx))
            else:
                if not project or not question:
                    raise ToolError("Para perguntar, informe `project` e `question`")
                body = QuestionCreate(**_given(question=question, context=context, options=options, card_id=card_id))
                saved = questions.ask_question(db, project_or_404(db, project), body, actor(ctx))
            return _dump(question_out(settings, saved))

    @mcp.tool()
    def session(
        ctx: Context,
        action: Literal["on", "off", "doing"],
        session: str | None = None,
        project: str | None = None,
        doing: str | None = None,
        card_id: int | None = None,
        cwd: str | None = None,
    ) -> dict:
        """Liga este chat ao board ("on"; sem `session`, gera uma chave: guarde e reuse), atualiza o "fazendo
        agora" ("doing", com `doing` e `card_id`) ou desliga ("off"). Aparece no painel Agora."""
        with db_for() as db:
            if action == "on":
                saved = sessions.upsert_session(
                    db, actor=actor(ctx), key=session, client="mcp", project=project, cwd=cwd, doing=doing,
                    card_id=card_id, active=True,
                )
            elif not session:
                raise ToolError('Informe `session` (a chave que voltou no action "on")')
            elif action == "off":
                saved = sessions.end_session(db, sessions.get_session(db, session))
            else:
                saved = sessions.update_session(
                    db, sessions.get_session(db, session), project=project, doing=doing, card_id=card_id, active=True
                )
            return {**_dump(session_out(settings, saved)), "status_line": sessions.status_line(settings, saved)}

    @mcp.prompt(name="board", description="Sincroniza esta conversa com o board e mostra o status em 3 linhas")
    def board(argument: str = "") -> str:
        return board_prompt(argument.strip() or "(nenhum)")

    return mcp


def mcp_routes(mcp: MCPServer, settings: Settings) -> list[BaseRoute]:
    """Rotas do /mcp para incluir na app FastAPI (o lifespan da app roda o session_manager)."""
    hosts = settings.hosts()
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[*hosts, *(f"{h}:*" for h in hosts)],
        allowed_origins=[settings.public_url, *(f"{scheme}://{h}:*" for h in hosts for scheme in ("http", "https"))],
    )
    # Com sessão (não stateless): o servidor lembra o clientInfo do initialize e usa o nome do cliente
    # ("claude-code", "cursor"...) como autor quando ele não manda X-Actor.
    app = mcp.streamable_http_app(streamable_http_path="/mcp", json_response=True, transport_security=security)
    return list(app.routes)
