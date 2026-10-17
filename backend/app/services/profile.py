"""Perfil do usuário desta instância: nome e foto opcional, guardados só na máquina dele."""

import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..db import utcnow
from ..models import Profile
from ..schemas import ProfileUpdate

AVATAR_PATTERN = re.compile(r"^data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/]+=*$")
# 300 KB de imagem viram ~400 mil caracteres em base64. A interface já reduz a foto para 160 px.
AVATAR_MAX_CHARS = 400_000


def get_profile(db: Session) -> Profile:
    return db.get(Profile, 1) or Profile(id=1, name="", avatar="", updated_at=None)


def update_profile(db: Session, body: ProfileUpdate) -> Profile:
    profile = db.get(Profile, 1)
    if profile is None:
        profile = Profile(id=1, name="", avatar="")
        db.add(profile)
    if body.name is not None:
        profile.name = body.name.strip()
    if body.avatar is not None:
        avatar = body.avatar.strip()
        if avatar and (len(avatar) > AVATAR_MAX_CHARS or not AVATAR_PATTERN.match(avatar)):
            raise HTTPException(422, "Foto inválida: mande uma data URL png, jpeg ou webp de até 300 KB")
        profile.avatar = avatar
    profile.updated_at = utcnow()
    db.commit()
    return profile
