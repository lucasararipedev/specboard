def test_filter_cards_by_one_or_many_labels(client, project):
    slug = project["slug"]
    stripe = client.post(f"/api/projects/{slug}/cards", json={"title": "Stripe", "labels": ["v0.2", "pagamentos"]}).json()
    login = client.post(f"/api/projects/{slug}/cards", json={"title": "Login", "labels": ["v0.2", "front"]}).json()
    client.post(f"/api/projects/{slug}/cards", json={"title": "Solto", "labels": ["front"]})

    v02 = client.get(f"/api/projects/{slug}/cards?label=v0.2").json()
    assert {c["id"] for c in v02} == {stripe["id"], login["id"]}
    # Várias etiquetas: o card precisa ter todas (sem diferenciar maiúsculas).
    both = client.get(f"/api/projects/{slug}/cards?label=V0.2&label=front").json()
    assert [c["id"] for c in both] == [login["id"]]
    found = client.get("/api/search?q=stripe&label=pagamentos").json()
    assert [c["id"] for c in found] == [stripe["id"]]
    assert client.get("/api/search?q=stripe&label=front").json() == []


def test_project_lists_labels_in_use(client, project):
    slug = project["slug"]
    client.post(f"/api/projects/{slug}/cards", json={"title": "A", "labels": ["v0.2", "bug"]})
    client.post(f"/api/projects/{slug}/cards", json={"title": "B", "labels": ["v0.2"]})
    assert client.get(f"/api/projects/{slug}/labels").json() == {"v0.2": 2, "bug": 1}
    assert client.get(f"/api/projects/{slug}").json()["labels"] == {"v0.2": 2, "bug": 1}


def test_briefing_lines_show_labels(client, project):
    slug = project["slug"]
    client.post(f"/api/projects/{slug}/cards", json={"title": "Stripe", "status": "todo", "labels": ["v0.2"]})
    assert "Stripe (v0.2)" in client.get(f"/api/projects/{slug}/briefing").text
