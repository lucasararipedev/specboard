"""Regras dos projetos, usadas pela API REST e pelo MCP."""

import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Activity, Project
from ..schemas import ProjectCreate, ProjectUpdate
from .questions import add_starter_questions


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:64].strip("-") or "projeto"


def unique_slug(db: Session, base: str) -> str:
    slug, n = base, 2
    while db.scalar(select(Project.id).where(Project.slug == slug)) is not None:
        suffix = f"-{n}"
        slug, n = base[: 64 - len(suffix)] + suffix, n + 1
    return slug


def list_projects(db: Session, include_archived: bool = False) -> list[Project]:
    query = select(Project).order_by(Project.updated_at.desc())
    if not include_archived:
        query = query.where(Project.archived.is_(False))
    return list(db.scalars(query))


def create_project(db: Session, body: ProjectCreate, actor: str) -> Project:
    if body.slug and db.scalar(select(Project.id).where(Project.slug == body.slug)) is not None:
        raise HTTPException(409, f"Já existe um projeto com o slug '{body.slug}'")
    project = Project(
        slug=body.slug or unique_slug(db, slugify(body.name)),
        name=body.name,
        summary=body.summary,
        spec=body.spec,
        repo=body.repo,
    )
    db.add(project)
    db.flush()
    if body.starter_questions:
        add_starter_questions(db, project.id)
    db.add(Activity(project_id=project.id, actor=actor, kind="created", message=f'Criou o projeto "{project.name}"'))
    db.commit()
    return project


def update_project(db: Session, project: Project, body: ProjectUpdate, actor: str) -> Project:
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if "spec" in changes and changes["spec"] != project.spec:
        db.add(Activity(project_id=project.id, actor=actor, kind="spec", message="Atualizou a spec"))
    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    return project
