"""Configuração lida de variáveis de ambiente (todas opcionais)."""

import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    # SQLite por padrão: um arquivo, zero serviço extra. Qualquer URL do SQLAlchemy funciona.
    database_url: str = "sqlite:///./data/specboard.db"
    # URL que a IA usa e repassa ao usuário nos links de board e card.
    public_url: str = "http://localhost:8787"
    # Se definido, toda a API (menos health, guia e prompt) exige "Authorization: Bearer <token>".
    api_token: str | None = None
    # Pasta com o build do front. No Docker o FastAPI serve o front e a API na mesma porta.
    static_dir: str | None = None
    # Card em "doing" ou "blocked" sem atualização há mais que isso aparece como parado no briefing.
    stale_days: int = 3
    # Hosts aceitos além de localhost/127.0.0.1 e do host da public_url (ex.: IP na rede local).
    # Barra DNS rebinding: um site malicioso não consegue falar com a API usando outro nome.
    allowed_hosts: tuple[str, ...] = ()

    def hosts(self) -> list[str]:
        public = urlsplit(self.public_url).hostname or "localhost"
        return sorted({"localhost", "127.0.0.1", public, *self.allowed_hosts})


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv("SPECBOARD_DATABASE_URL", Settings.database_url),
        public_url=os.getenv("SPECBOARD_PUBLIC_URL", Settings.public_url).rstrip("/"),
        api_token=os.getenv("SPECBOARD_TOKEN") or None,
        static_dir=os.getenv("SPECBOARD_STATIC_DIR") or None,
        stale_days=int(os.getenv("SPECBOARD_STALE_DAYS", str(Settings.stale_days))),
        allowed_hosts=tuple(h.strip() for h in os.getenv("SPECBOARD_ALLOWED_HOSTS", "").split(",") if h.strip()),
    )
