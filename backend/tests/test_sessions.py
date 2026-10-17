from datetime import timedelta

from app.db import utcnow
from app.models import AgentSession


def hook(client, event, session_id="abc123", **extra):
    res = client.post("/api/hooks/claude-code", json={"hook_event_name": event, "session_id": session_id, **extra})
    assert res.status_code == 200
    return res.json()


def test_session_start_in_project_folder_turns_on(client):
    project = client.post("/api/projects", json={"name": "Meu SaaS", "repo": "~/code/meu-saas"}).json()
    out = hook(client, "SessionStart", cwd="/home/ana/code/meu-saas/backend", source="startup")
    assert out["systemMessage"].startswith("Specboard ativo neste chat · projeto meu-saas")
    context = out["hookSpecificOutput"]["additionalContext"]
    assert 'sessão "abc123"' in context and "Briefing do Specboard" in context

    sessions = client.get("/api/sessions").json()
    assert [(s["key"], s["project"], s["active"]) for s in sessions] == [("abc123", project["slug"], True)]


def test_session_start_elsewhere_stays_off(client, project):
    out = hook(client, "SessionStart", cwd="/tmp/rascunho")
    assert "systemMessage" not in out
    assert "desligado neste chat" in out["hookSpecificOutput"]["additionalContext"]
    assert client.get("/api/sessions").json() == []
    # /board liga a mesma sessão pela API (ou pelo MCP).
    on = client.post("/api/sessions", json={"key": "abc123", "project": project["slug"], "doing": "Revisando"}).json()
    assert on["active"] and on["project"] == project["slug"] and on["doing"] == "Revisando"


def test_stop_is_heartbeat_and_session_end_closes(client, make_client):
    client.post("/api/projects", json={"name": "App", "repo": "/work/app"})
    hook(client, "SessionStart", cwd="/work/app")
    with client.app.state.sessionmaker() as db:
        s = db.query(AgentSession).one()
        s.last_seen_at = utcnow() - timedelta(hours=1)
        db.commit()
    assert client.get("/api/sessions").json()[0]["idle"] is True
    hook(client, "Stop")
    assert client.get("/api/sessions").json()[0]["idle"] is False
    hook(client, "SessionEnd")
    assert client.get("/api/sessions").json() == []
    assert hook(client, "Whatever") == {}


def test_doing_and_card_show_in_briefing(client, project):
    slug = project["slug"]
    card = client.post(f"/api/projects/{slug}/cards", json={"title": "Login"}).json()
    s = client.post("/api/sessions", json={"project": slug}).json()
    client.patch(f"/api/sessions/{s['key']}", json={"doing": "Corrigindo o login", "card_id": card["id"]})
    listed = client.get(f"/api/sessions?project={slug}").json()[0]
    assert listed["card_url"] == card["url"] and listed["actor"] == "claude"
    assert f"- claude: Corrigindo o login (#{card['id']})" in client.get("/api/briefing").text
    assert client.delete(f"/api/sessions/{s['key']}").json()["active"] is False


def test_match_project_by_folder_name_when_unique(client):
    client.post("/api/projects", json={"name": "Loja", "repo": "https://github.com/ana/loja.git"})
    out = hook(client, "SessionStart", cwd="C:\\Users\\ana\\loja")
    assert "projeto loja" in out["systemMessage"]


def test_hook_requires_token(make_client):
    client = make_client(api_token="segredo")
    res = client.post("/api/hooks/claude-code", json={"hook_event_name": "Stop", "session_id": "x"})
    assert res.status_code == 401
