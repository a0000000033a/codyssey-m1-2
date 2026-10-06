import pytest


def test_record_crud_and_same_date_multiple(api):
    client, services = api
    payload = {"symbol": "005930", "date": "2026-09-01", "value": 150, "memo": "관심 가격"}
    first = client.post("/api/data", json=payload)
    assert first.status_code == 201
    id = first.json()["id"]
    assert client.post("/api/data", json=payload).status_code == 201
    listed = client.get("/api/data", params={"symbol": "005930", "limit": 1}).json()
    assert len(listed["items"]) == 1
    assert listed["next_cursor"]
    assert client.put(f"/api/data/{id}", json=dict(payload, value=160)).json()["value"] == 160
    assert client.delete(f"/api/data/{id}").status_code == 204
    assert len(client.get("/api/data?symbol=005930").json()["items"]) == 1


@pytest.mark.parametrize("change", [{"date": "2099-01-01"}, {"value": 0}, {"value": -1}, {"value": "NaN"}, {"value": "Infinity"}, {"memo": "x"*1001}, {"symbol": "bad"}, {"owner_uid": "other"}])
def test_bad_record_inputs_are_rejected(api, change):
    client, _ = api
    r = client.post("/api/data", json=dict({"symbol": "005930", "date": "2026-09-01", "value": 100, "memo": ""}, **change))
    assert r.status_code == 422


def test_other_owner_record_cannot_be_modified(api):
    client, services = api
    services.repo.put("data", "foreign", {"owner_uid": "other", "symbol": "005930"})
    assert client.delete("/api/data/foreign").status_code == 404


def test_summary_route_and_invalid_cursor(api):
    client, _ = api
    summary = client.get("/api/data/summary?symbol=005930")
    assert summary.status_code == 200
    assert summary.json()["market_data"]["count"] == 2
    assert client.get("/api/data?symbol=005930&cursor=broken").status_code == 400
