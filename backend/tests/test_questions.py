from app.services.questions import STARTER_QUESTIONS


def test_new_project_starts_with_questions(client, project):
    questions = client.get(f"/api/projects/{project['slug']}/questions").json()
    assert [q["question"] for q in questions] == [q["question"] for q in STARTER_QUESTIONS]
    assert all(q["status"] == "open" and q["asked_by"] == "specboard" for q in questions)
    assert project["open_questions"] == len(STARTER_QUESTIONS)


def test_starter_questions_can_be_skipped(client):
    project = client.post("/api/projects", json={"name": "Sem perguntas", "starter_questions": False}).json()
    assert project["open_questions"] == 0


def test_question_lifecycle(client, project):
    slug = project["slug"]
    card = client.post(f"/api/projects/{slug}/cards", json={"title": "Stripe"}).json()
    q = client.post(
        f"/api/projects/{slug}/questions",
        json={"question": "Mensal ou anual?", "options": ["Mensal", "Anual"], "card_id": card["id"]},
    ).json()
    assert q["status"] == "open"
    assert q["asked_by"] == "claude"
    assert q["url"].endswith(f"/p/{slug}?tab=perguntas&q={q['id']}")

    # Ainda sem resposta, não dá para marcar como usada.
    assert client.patch(f"/api/questions/{q['id']}", json={"status": "applied"}).status_code == 422

    answered = client.patch(
        f"/api/questions/{q['id']}", json={"answer": "Só mensal"}, headers={"X-Actor": "user"}
    ).json()
    assert answered["status"] == "answered"
    assert answered["answered_at"] is not None

    briefing = client.get(f"/api/projects/{slug}/briefing", params={"format": "json"}).json()["projects"][0]
    assert [a["answer"] for a in briefing["new_answers"]] == ["Só mensal"]
    assert any("resposta(s) nova(s)" in n for n in briefing["nudges"])
    assert "Respostas novas" in client.get(f"/api/projects/{slug}/briefing").text

    applied = client.patch(f"/api/questions/{q['id']}", json={"status": "applied"}).json()
    assert applied["status"] == "applied"
    briefing = client.get(f"/api/projects/{slug}/briefing", params={"format": "json"}).json()["projects"][0]
    assert briefing["new_answers"] == []

    log = client.get(f"/api/projects/{slug}/activity", params={"card_id": card["id"]}).json()
    assert {a["kind"] for a in log} >= {"question", "answer"}


def test_clearing_answer_reopens(client, project):
    qid = client.get(f"/api/projects/{project['slug']}/questions").json()[0]["id"]
    client.patch(f"/api/questions/{qid}", json={"answer": "Devs solo"})
    reopened = client.patch(f"/api/questions/{qid}", json={"answer": "  "}).json()
    assert reopened["status"] == "open"
    assert reopened["answered_at"] is None


def test_open_questions_nudge_points_to_tab(client, project):
    nudges = client.get("/api/briefing", params={"format": "json"}).json()["projects"][0]["nudges"]
    assert any(f"/p/{project['slug']}?tab=perguntas" in n for n in nudges)


def test_question_card_must_belong_to_project(client, project):
    other = client.post("/api/projects", json={"name": "Outro"}).json()
    card = client.post(f"/api/projects/{other['slug']}/cards", json={"title": "X"}).json()
    res = client.post(f"/api/projects/{project['slug']}/questions", json={"question": "?", "card_id": card["id"]})
    assert res.status_code == 404
