import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.services.agent_docs import board_prompt

REPO_ROOT = Path(__file__).resolve().parents[2]
HEADERS = {"Accept": "application/json, text/event-stream", "X-Actor": "claude"}


@pytest.fixture
def mcp(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path}/mcp.db"))
    # O lifespan (com o session_manager do MCP) só roda dentro do "with".
    with TestClient(app, base_url="http://localhost") as client:
        ids = iter(range(1, 1000))
        session: dict[str, str] = {}

        def rpc(method: str, params: dict | None = None, headers: dict | None = None):
            body = {"jsonrpc": "2.0", "id": next(ids), "method": method, "params": params or {}}
            res = client.post("/mcp", json=body, headers={**HEADERS, **session, **(headers or {})})
            assert res.status_code == 200, res.text
            if "mcp-session-id" in res.headers:
                session["mcp-session-id"] = res.headers["mcp-session-id"]
            data = res.json()
            assert "error" not in data, data
            return data["result"]

        rpc.client = client
        rpc(
            "initialize",
            {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "teste", "version": "1"}},
        )
        client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers={**HEADERS, **session}
        )
        yield rpc


def call(rpc, tool: str, **arguments):
    return rpc("tools/call", {"name": tool, "arguments": arguments})


def data(result):
    """As tools devolvem JSON no texto do conteúdo."""
    assert not result.get("isError"), result
    return json.loads(result["content"][0]["text"])


def items(result):
    """Tool que devolve lista: um bloco de conteúdo por item."""
    assert not result.get("isError"), result
    return [json.loads(block["text"]) for block in result["content"]]


def test_lists_tools_and_board_prompt(mcp):
    names = {t["name"] for t in mcp("tools/list")["tools"]}
    assert {"briefing", "save_card", "list_cards", "session"} <= names
    assert not any("release" in n for n in names)
    prompt = mcp("prompts/get", {"name": "board", "arguments": {"argument": "off"}})
    assert "Argumento: off" in prompt["messages"][0]["content"]["text"]


def test_save_card_creates_with_activity_and_url(mcp):
    project = data(call(mcp, "save_project", name="Meu SaaS", repo="~/code/meu-saas"))
    card = data(call(mcp, "save_card", project=project["slug"], title="Stripe", status="todo", labels=["v0.2"]))
    assert card["labels"] == ["v0.2"] and card["url"].endswith(f"?card={card['id']}")

    moved = data(call(mcp, "save_card", card_id=card["id"], status="doing"))
    assert moved["status"] == "doing" and moved["labels"] == ["v0.2"]
    assert [c["id"] for c in items(call(mcp, "list_cards", project="meu-saas", labels=["v0.2"]))] == [card["id"]]
    assert data(call(mcp, "get_project", project="meu-saas"))["labels"] == {"v0.2": 1}

    log = mcp.client.get("/api/projects/meu-saas/activity").json()
    assert {a["actor"] for a in log} == {"claude"}
    assert "Stripe (v0.2)" in call(mcp, "briefing", project="meu-saas")["content"][0]["text"]


def test_errors_come_back_as_tool_errors(mcp):
    result = call(mcp, "save_card", project="nao-existe", title="X")
    assert result["isError"] is True
    assert "não existe" in result["content"][0]["text"]


def test_session_on_doing_off(mcp):
    call(mcp, "save_project", name="App")
    on = data(call(mcp, "session", action="on", project="app", doing="Lendo a spec"))
    assert on["active"] and on["status_line"].startswith("Specboard ativo neste chat · projeto app")
    key = on["key"]
    call(mcp, "session", action="doing", session=key, doing="Escrevendo testes")
    assert mcp.client.get("/api/sessions").json()[0]["doing"] == "Escrevendo testes"
    call(mcp, "session", action="off", session=key)
    assert mcp.client.get("/api/sessions").json() == []


def test_actor_falls_back_to_client_name(mcp):
    res = mcp("tools/call", {"name": "save_project", "arguments": {"name": "Outro"}}, headers={"X-Actor": ""})
    assert not res.get("isError")
    log = mcp.client.get("/api/projects/outro/activity").json()
    assert log[-1]["actor"] == "teste"


def test_mcp_requires_token(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path}/t.db", api_token="segredo"))
    with TestClient(app, base_url="http://localhost") as client:
        res = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, headers=HEADERS)
        assert res.status_code == 401


def test_plugin_command_matches_board_prompt():
    command = (REPO_ROOT / "integrations/claude-code/commands/board.md").read_text(encoding="utf-8")
    body = command.split("---", 2)[2].lstrip("\n")
    assert body == board_prompt("$ARGUMENTS")
