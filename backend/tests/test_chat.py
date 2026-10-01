from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest


def payload(**changes):
    return dict({"symbol": "005930", "message": "최근 흐름을 설명해주세요.", "request_id": str(uuid4())}, **changes)


def test_successful_retry_does_not_call_model_twice(api):
    client, services = api
    body = payload()
    first = client.post("/api/chat", json=body)
    assert first.status_code == 200
    retry = client.post("/api/chat", json=body)
    assert retry.json()["conversation_id"] == first.json()["conversation_id"]
    id = first.json()["conversation_id"]
    assert len(client.get(f"/api/conversations/{id}").json()["messages"]) == 2
    assert services.ai.calls == 1
    assert first.json()["context"]["stock"]["symbol"] == "005930"
    assert client.post("/api/chat", json=dict(body, message="다른 질문")).status_code == 409


def test_symbol_mismatch_and_other_owner(api):
    client, services = api
    id = client.post("/api/conversations", json={"symbol": "005930"}).json()["id"]
    assert client.post("/api/chat", json=payload(symbol="000660", conversation_id=id)).status_code == 400
    services.repo.put("conversations", "foreign", {"owner_uid": "other"})
    assert client.post("/api/chat", json=payload(conversation_id="foreign")).status_code == 404
    assert services.ai.calls == 0


def test_model_failure_releases_lock_without_saving_messages(api):
    client, services = api
    services.ai.fail = True
    body = payload()
    assert client.post("/api/chat", json=body).status_code == 502
    services.ai.fail = False
    result = client.post("/api/chat", json=body)
    assert result.status_code == 200
    assert len(client.get(f"/api/conversations/{result.json()['conversation_id']}").json()["messages"]) == 2


def test_deleting_conversation_and_pending_turn_are_rejected(api):
    client, services = api
    id = client.post("/api/conversations", json={"symbol": "005930"}).json()["id"]
    row = services.repo.get("conversations", id)
    row["pending"] = {"request_key": "other", "lease_until": (datetime.now(timezone.utc)+timedelta(seconds=90)).isoformat()}
    services.repo.put("conversations", id, row)
    assert client.post("/api/chat", json=payload(conversation_id=id)).status_code == 409
    row["pending"]["lease_until"] = (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
    services.repo.put("conversations", id, row)
    assert client.post("/api/chat", json=payload(conversation_id=id)).status_code == 200
    row = services.repo.get("conversations", id)
    row["status"] = "deleting"
    services.repo.put("conversations", id, row)
    assert client.post("/api/chat", json=payload(conversation_id=id)).status_code == 409


def test_save_failure_is_reported_and_retry_does_not_recall_model(api, monkeypatch):
    client, services = api
    original = services.repo.put
    def broken(collection, id, value):
        if collection.endswith("/messages"):
            raise RuntimeError("persist error")
        return original(collection, id, value)
    monkeypatch.setattr(services.repo, "put", broken)
    body = payload()
    assert client.post("/api/chat", json=body).status_code == 503
    assert client.post("/api/chat", json=body).status_code == 409
    assert services.ai.calls == 1


def test_delete_during_model_call_cannot_recreate_conversation(api):
    client, services = api
    id = client.post("/api/conversations", json={"symbol": "005930"}).json()["id"]
    services.ai.on_answer = lambda: services.conversations.delete("owner", id)
    assert client.post("/api/chat", json=payload(conversation_id=id)).status_code == 404
    assert services.repo.get("conversations", id) is None
    assert services.repo.list(f"conversations/{id}/messages") == []
