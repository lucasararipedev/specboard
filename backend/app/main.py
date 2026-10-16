"""Entrada da aplicação: API em /api, manual da IA em /llms.txt e, no Docker, o front buildado em /."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import sessionmaker

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

    # Libera o front em dev (Vite em outra porta). Em produção front e API dividem a origem.
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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


def _serve_frontend(app: FastAPI, static: Path) -> None:
    root = static.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        file = (root / path).resolve()
        if path and file.is_file() and file.is_relative_to(root):
            return FileResponse(file)
        # Rotas do Vue Router (/p/<slug>, /conectar) caem no index.html.
        return FileResponse(root / "index.html")
