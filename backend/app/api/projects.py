from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..config import Settings
from ..deps import get_actor, get_db, get_settings, project_or_404, require_token
from ..schemas import ProjectCreate, ProjectDetail, ProjectOut, ProjectUpdate
from ..services import projects as service
from ..services.serialize import label_counts, project_out

router = APIRouter(prefix="/api/projects", tags=["projects"], dependencies=[Depends(require_token)])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return [project_out(db, settings, p) for p in service.list_projects(db, include_archived)]


@router.post("", response_model=ProjectDetail, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    return project_out(db, settings, service.create_project(db, body, actor), detail=True)


@router.get("/{slug}", response_model=ProjectDetail)
def get_project(slug: str, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    return project_out(db, settings, project_or_404(db, slug), detail=True)


@router.get("/{slug}/spec", response_class=Response, responses={200: {"content": {"text/markdown": {}}}})
def get_spec(slug: str, db: Session = Depends(get_db)):
    """A spec em Markdown puro, pronta para a IA ler."""
    return Response(project_or_404(db, slug).spec, media_type="text/markdown; charset=utf-8")


@router.get("/{slug}/labels")
def get_labels(slug: str, db: Session = Depends(get_db)) -> dict[str, int]:
    """Etiquetas em uso no projeto, com quantos cards têm cada uma. Reaproveite antes de criar uma nova."""
    return label_counts(db, project_or_404(db, slug).id)


@router.patch("/{slug}", response_model=ProjectDetail)
def update_project(
    slug: str,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: str = Depends(get_actor),
):
    project = service.update_project(db, project_or_404(db, slug), body, actor)
    return project_out(db, settings, project, detail=True)


@router.delete("/{slug}", status_code=204)
def delete_project(slug: str, db: Session = Depends(get_db)):
    """Apaga o projeto com cards e atividades. Para só esconder, use PATCH {"archived": true}."""
    db.delete(project_or_404(db, slug))
    db.commit()
