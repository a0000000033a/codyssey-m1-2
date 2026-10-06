import pytest


def create(client, content="첫 대화 질문"):
    r = client.post("/api/conversations", json={"symbol": "005930", "messages": [{"role": "user", "content": content}]})
    assert r.status_code == 201
    return r.json()


def test_two_conversations_for_same_symbol(api):
    client, _ = api
    first, second = create(client), create(client, "두 번째 질문")
    assert first["id"] != second["id"]
    detail = client.get(f"/api/conversations/{first['id']}").json()
    assert detail["messages"][0]["content"] == "첫 대화 질문"
    listing = client.get("/api/conversations?symbol=005930").json()
    assert len(listing["items"]) == 2
    assert "messages" not in listing["items"][0]


@pytest.mark.parametrize("messages", [[{"role": "system", "content": "bad"}], [{"role": "user", "content": "a"*8001}], [{"role": "user", "content": "a"}]*101])
def test_invalid_manual_messages(api, messages):
    client, _ = api
    assert client.post("/api/conversations", json={"symbol": "005930", "messages": messages}).status_code == 422


def test_delete_removes_messages_and_not_watchlist(api):
    client, services = api
    id = create(client)["id"]
    assert services.repo.list(f"conversations/{id}/messages")
    assert client.delete(f"/api/conversations/{id}").status_code == 204
    assert services.repo.list(f"conversations/{id}/messages") == []
    assert client.get(f"/api/conversations/{id}").status_code == 404


def test_partial_delete_can_be_retried(api, monkeypatch):
    client, services = api
    id = create(client)["id"]
    original = services.repo.delete
    failed = [False]
    def interrupted(collection, doc_id):
        if collection.endswith("/messages") and not failed[0]:
            failed[0] = True
            raise RuntimeError("storage interrupted")
        return original(collection, doc_id)
    monkeypatch.setattr(services.repo, "delete", interrupted)
    assert client.delete(f"/api/conversations/{id}").status_code == 503
    assert services.repo.get("conversations", id)["status"] == "deleting"
    assert client.delete(f"/api/conversations/{id}").status_code == 204


def test_ownership_and_watchlist_removal(api):
    client, services = api
    id = create(client)["id"]
    watch = client.post("/api/watchlist", json={"symbol": "005930"}).json()
    assert client.delete(f"/api/watchlist/{watch['id']}").status_code == 204
    assert client.get(f"/api/conversations/{id}").status_code == 200
    services.repo.put("conversations", "foreign", {"owner_uid": "other"})
    assert client.get("/api/conversations/foreign").status_code == 404
    assert client.delete("/api/conversations/foreign").status_code == 404
