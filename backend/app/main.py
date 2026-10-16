"""Entrada da aplicação: API em /api, manual da IA em /llms.txt e, no Docker, o front buildado em /."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import sessionmaker
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .api import activity, agent, cards, projects, questions
from .config import Settings, load_settings
from .db import Base, make_engine

DESCRIPTION = """Kanban spec-first para a sua IA manter seus projetos organizados.

Se você é uma IA, comece por **GET /llms.txt**: tem as regras e exemplos."""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    engine = make_engine(settings.database_url)
    # Esquema pequeno e estável na v1: create_all basta. Migrações (Alembic) entram quando o esquema mudar.
    Base.metadata.create_all(engine)

    app = FastAPI(title="Specboard", version="0.1.0", description=DESCRIPTION)
    app.state.settings = settings
    app.state.sessionmaker = sessionmaker(engine, expire_on_commit=False)

    # Sem CORS de propósito: front e API dividem a origem (em dev o Vite faz proxy) e a IA usa curl. Com CORS
    # aberto, qualquer site aberto no navegador leria e mudaria os dados em localhost.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts())

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    @app.get("/api/health", tags=["meta"])
    def health():
        return {"ok": True}

    for module in (projects, cards, questions, activity):
        app.include_router(module.router)
    app.include_router(agent.router)
    app.include_router(agent.public)

    if settings.static_dir and Path(settings.static_dir, "index.html").exists():
        _serve_frontend(app, Path(settings.static_dir))

    return app


# Só a interface (o /docs usa Swagger de CDN). Imagens externas liberadas porque a spec pode citar prints.
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; img-src 'self' data: https:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)


def _serve_frontend(app: FastAPI, static: Path) -> None:
    root = static.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        file = (root / path).resolve()
        if path and file.is_file() and file.is_relative_to(root):
            return FileResponse(file)
        # Rotas do Vue Router (/, /projetos, /p/<slug>) caem no index.html.
        return FileResponse(root / "index.html", headers={"Content-Security-Policy": CSP})
