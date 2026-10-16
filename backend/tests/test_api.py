from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.config import Settings
from app.db import utcnow
from app.models import Card
from app.services.agent_docs import agent_prompt

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_project_slug_is_generated_and_unique(client):
    a = client.post("/api/projects", json={"name": "Integração Pix"}).json()
    b = client.post("/api/projects", json={"name": "Integração Pix"}).json()
    assert a["slug"] == "integracao-pix"
    assert b["slug"] == "integracao-pix-2"
    assert a["url"] == "http://localhost:8787/p/integracao-pix"


def test_explicit_slug_conflict(client, project):
    res = client.post("/api/projects", json={"name": "Outro", "slug": project["slug"]})
    assert res.status_code == 409


def test_card_lifecycle_logs_activity(client, project):
    slug = project["slug"]
    card = client.post(f"/api/projects/{slug}/cards", json={"title": "Login", "status": "todo", "priority": 1}).json()
    assert card["status"] == "todo"
    assert card["url"].endswith(f"/p/{slug}?card={card['id']}")

    doing = client.patch(f"/api/cards/{card['id']}", json={"status": "doing"}).json()
    assert doing["started_at"] is not None
    done = client.patch(f"/api/cards/{card['id']}", json={"status": "done"}).json()
    assert done["done_at"] is not None

    log = client.get(f"/api/projects/{slug}/activity").json()
    messages = [a["message"] for a in log]
    assert messages[0] == f'#{card["id"]} "Login": doing → done'
    assert all(a["actor"] == "claude" for a in log)


def test_moving_card_goes_to_end_of_column(client, project):
    slug = project["slug"]
    first = client.post(f"/api/projects/{slug}/cards", json={"title": "A", "status": "todo"}).json()
    second = client.post(f"/api/projects/{slug}/cards", json={"title": "B"}).json()
    moved = client.patch(f"/api/cards/{second['id']}", json={"status": "todo"}).json()
    assert moved["position"] > first["position"]


def test_due_date_can_be_cleared(client, project):
    card = client.post(
        f"/api/projects/{project['slug']}/cards", json={"title": "Deploy", "due_date": "2026-11-01"}
    ).json()
    cleared = client.patch(f"/api/cards/{card['id']}", json={"due_date": None, "title": None}).json()
    assert cleared["due_date"] is None
    assert cleared["title"] == "Deploy"


def test_spec_update_is_logged_and_served_as_markdown(client, project):
    slug = project["slug"]
    client.patch(f"/api/projects/{slug}", json={"spec": "# Meu SaaS\n\n## 1. Problema"})
    res = client.get(f"/api/projects/{slug}/spec")
    assert res.headers["content-type"].startswith("text/markdown")
    assert res.text.startswith("# Meu SaaS")
    kinds = [a["kind"] for a in client.get(f"/api/projects/{slug}/activity").json()]
    assert "spec" in kinds


def test_activity_rejects_card_from_other_project(client, project):
    other = client.post("/api/projects", json={"name": "Outro"}).json()
    card = client.post(f"/api/projects/{other['slug']}/cards", json={"title": "X"}).json()
    res = client.post(f"/api/projects/{project['slug']}/activity", json={"message": "oi", "card_id": card["id"]})
    assert res.status_code == 404


def test_search_is_case_insensitive(client, project):
    client.post(f"/api/projects/{project['slug']}/cards", json={"title": "Integrar Stripe"})
    assert [c["title"] for c in client.get("/api/search", params={"q": "stripe"}).json()] == ["Integrar Stripe"]


def test_briefing_nudges(client, project):
    slug = project["slug"]
    urgent = client.post(f"/api/projects/{slug}/cards", json={"title": "Bug no checkout", "priority": 0}).json()
    nxt = client.post(f"/api/projects/{slug}/cards", json={"title": "Onboarding", "status": "todo"}).json()
    late = client.post(
        f"/api/projects/{slug}/cards",
        json={"title": "Pitch", "status": "todo", "due_date": (date.today() - timedelta(days=2)).isoformat()},
    ).json()

    data = client.get("/api/briefing", params={"format": "json"}).json()
    p = data["projects"][0]
    nudges = "\n".join(p["nudges"])
    assert "sem spec" in nudges
    assert f"#{urgent['id']}" in nudges and "backlog" in nudges
    assert f"#{late['id']}" in nudges and "venceu" in nudges
    assert "Nada em andamento" in nudges
    assert [c["id"] for c in p["next_up"]] == [nxt["id"], late["id"]]

    md = client.get("/api/briefing").text
    assert "## Meu SaaS (`meu-saas`)" in md
    assert "Lembretes para puxar com o usuário" in md


def test_briefing_flags_stale_cards(client, project):
    card = client.post(f"/api/projects/{project['slug']}/cards", json={"title": "Refator", "status": "doing"}).json()
    with client.app.state.sessionmaker() as db:
        db.get(Card, card["id"]).updated_at = utcnow() - timedelta(days=5)
        db.commit()
    nudges = client.get("/api/briefing", params={"format": "json"}).json()["projects"][0]["nudges"]
    assert any(f"#{card['id']}" in n and "5 dias" in n for n in nudges)


def test_archived_projects_leave_briefing(client, project):
    client.patch(f"/api/projects/{project['slug']}", json={"archived": True})
    assert client.get("/api/projects").json() == []
    assert client.get("/api/briefing", params={"format": "json"}).json()["projects"] == []


def test_token_protects_api_but_not_guide(make_client):
    client = make_client(api_token="segredo")
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects", headers={"Authorization": "Bearer segredo"}).status_code == 200
    assert client.get("/llms.txt").status_code == 200
    prompt = client.get("/api/agent/prompt").text
    assert "segredo" not in prompt and "Authorization" in prompt


def test_datetimes_are_utc(client, project):
    created = datetime.fromisoformat(client.get(f"/api/projects/{project['slug']}").json()["created_at"])
    assert created.utcoffset() == timedelta(0)
    assert abs(datetime.now(timezone.utc) - created) < timedelta(minutes=1)


def test_prompt_md_matches_default_prompt():
    """PROMPT.md (para copiar do GitHub) tem que ser igual ao prompt servido pela instância padrão."""
    assert (REPO_ROOT / "PROMPT.md").read_text() == agent_prompt(Settings())


def test_prompt_is_one_text_for_any_ai(client):
    """Um prompt só para qualquer IA, apontando para a lista de projetos (a raiz é a página inicial)."""
    prompt = client.get("/api/agent/prompt").text
    assert "/projetos" in prompt
    assert not any(tool in prompt for tool in ("CLAUDE.md", "Cursor", "Gem "))
    assert client.get("/api/briefing", params={"format": "json"}).json()["board_url"].endswith("/projetos")


def test_other_sites_cannot_use_the_api(client):
    """Sem CORS: um site aberto no navegador não lê nem muda os dados em localhost."""
    evil = {"Origin": "https://site-malicioso.example"}
    assert "access-control-allow-origin" not in client.get("/api/projects", headers=evil).headers
    preflight = client.options(
        "/api/projects", headers={**evil, "Access-Control-Request-Method": "POST"}
    )
    assert "access-control-allow-origin" not in preflight.headers


def test_unknown_host_is_rejected(make_client):
    """DNS rebinding: só localhost, 127.0.0.1, o host da public_url e SPECBOARD_ALLOWED_HOSTS."""
    client = make_client(public_url="https://board.exemplo.dev", allowed_hosts=("192.168.0.10",))
    assert client.get("/api/health", headers={"Host": "rebind.site-malicioso.example"}).status_code == 400
    for host in ("localhost:8787", "127.0.0.1:8787", "board.exemplo.dev", "192.168.0.10:8787"):
        assert client.get("/api/health", headers={"Host": host}).status_code == 200


def test_security_headers(client):
    headers = client.get("/api/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"


def test_interface_has_csp(make_client, tmp_path):
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<!doctype html><div id=app></div>")
    client = make_client(static_dir=str(static))
    csp = client.get("/projetos").headers["content-security-policy"]
    assert "frame-ancestors 'none'" in csp and "script-src 'self'" in csp
    assert client.get("/../../etc/passwd").status_code in (200, 404)
    assert "root:" not in client.get("/..%2F..%2Fetc%2Fpasswd").text


def test_prompt_and_guide_keep_the_board_private(client):
    """A IA não pode vazar planos do board para o repositório nem descrever plano como pronto."""
    prompt = client.get("/api/agent/prompt").text
    guide = client.get("/llms.txt").text
    for text in (prompt, guide):
        assert "privad" in text and "commit" in text
        assert "não invente" in text
    assert "não um arquivo do repositório" in guide
