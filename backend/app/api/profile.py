"""Perfil do usuário: nome e foto que aparecem no histórico, no topo e no briefing."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, require_token
from ..models import Profile
from ..schemas import ProfileOut, ProfileUpdate
from ..services import profile as service

router = APIRouter(prefix="/api/profile", tags=["profile"], dependencies=[Depends(require_token)])


def _out(profile: Profile) -> ProfileOut:
    return ProfileOut(name=profile.name, avatar=profile.avatar, updated_at=profile.updated_at)


@router.get("", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    return _out(service.get_profile(db))


@router.put("", response_model=ProfileOut)
def update_profile(body: ProfileUpdate, db: Session = Depends(get_db)):
    """Campos omitidos ficam como estão; `avatar: ""` remove a foto."""
    return _out(service.update_profile(db, body))
