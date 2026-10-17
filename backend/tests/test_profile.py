PIXEL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="


def test_profile_starts_empty_and_saves(client):
    assert client.get("/api/profile").json()["name"] == ""
    saved = client.put("/api/profile", json={"name": " Lucas ", "avatar": PIXEL}).json()
    assert saved["name"] == "Lucas" and saved["avatar"] == PIXEL
    # Campo omitido fica como está; "" remove a foto.
    client.put("/api/profile", json={"avatar": ""})
    after = client.get("/api/profile").json()
    assert after["name"] == "Lucas" and after["avatar"] == ""


def test_profile_rejects_invalid_avatar(client):
    assert client.put("/api/profile", json={"avatar": "javascript:alert(1)"}).status_code == 422
    assert client.put("/api/profile", json={"avatar": "data:image/svg+xml;base64,PHN2Zz4="}).status_code == 422
    big = "data:image/png;base64," + "A" * 400_001
    assert client.put("/api/profile", json={"avatar": big}).status_code == 422


def test_briefing_uses_profile_name(client, project):
    client.put("/api/profile", json={"name": "Lucas"})
    assert "Usuário: Lucas" in client.get("/api/briefing").text
