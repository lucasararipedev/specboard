import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..deps import get_actor, get_db, get_settings, project_or_404, require_token
from ..models import Activity, Project
from ..schemas import ProjectCreate, ProjectDetail, ProjectOut, ProjectUpdate
from ..services.questions import add_starter_questions
from ..services.serialize import project_out

router = APIRouter(prefix="/api/projects", tags=["projects"], dependencies=[Depends(require_token)])


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


@router.get("", response_model=list[ProjectOut])
def list_projects(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    query = select(Project).order_by(Project.updated_at.desc())
    if not include_archived:
        query = query.where(Project.archived.is_(False))
    return [project_out(db, settings, p) for p in db.scalars(query)]


@router.post("", response_model=ProjectDetail, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
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
    return project_out(db, settings, project, detail=True)


@router.get("/{slug}", response_model=ProjectDetail)
def get_project(slug: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return project_out(db, settings, project_or_404(db, slug), detail=True)


@router.get("/{slug}/spec", response_class=Response, responses={200: {"content": {"text/markdown": {}}}})
def get_spec(slug: str, db: Session = Depends(get_db)):
    """A spec em Markdown puro, pronta para a IA ler."""
    return Response(project_or_404(db, slug).spec, media_type="text/markdown; charset=utf-8")


@router.patch("/{slug}", response_model=ProjectDetail)
def update_project(
    slug: str,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    project = project_or_404(db, slug)
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if "spec" in changes and changes["spec"] != project.spec:
        db.add(Activity(project_id=project.id, actor=actor, kind="spec", message="Atualizou a spec"))
    for field, value in changes.items():
        setattr(project, field, value)
    db.commit()
    return project_out(db, settings, project, detail=True)


@router.delete("/{slug}", status_code=204)
def delete_project(slug: str, db: Session = Depends(get_db)):
    """Apaga o projeto com cards e atividades. Para só esconder, use PATCH {"archived": true}."""
    db.delete(project_or_404(db, slug))
    db.commit()
