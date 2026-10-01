import pytest
from fastapi.testclient import TestClient


def make_client():
    from app.main import create_app
    from app.core.config import Settings

    def verify(token):
        if token == "expired":
            raise ValueError("private upstream diagnostic")
        return {"uid": token}

    return TestClient(create_app(Settings(allowed_user_uid="owner", allowed_origins=["http://localhost:5500"]), token_verifier=verify))


def test_health_and_docs_are_public():
    client = make_client()
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/docs").status_code == 200


@pytest.mark.parametrize("token,status", [(None, 401), ("expired", 401), ("other", 403), ("owner", 200)])
def test_owner_only_api(token, status):
    client = make_client()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get("/api/me", headers=headers)
    assert response.status_code == status
    assert "private upstream diagnostic" not in response.text


def test_cors_does_not_allow_unknown_origin():
    client = make_client()
    for origin, expected in [("http://localhost:5500", 200), ("https://untrusted.test", 400)]:
        r = client.options("/api/me", headers={"Origin": origin, "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"})
        assert r.status_code == expected
        if expected == 200:
            assert r.headers["access-control-allow-origin"] == origin
        else:
            assert "access-control-allow-origin" not in r.headers


def test_missing_owner_fails_closed():
    from app.core.config import Settings
    from app.main import create_app
    client = TestClient(create_app(Settings(), token_verifier=lambda _: {"uid": "owner"}))
    assert client.get("/api/me", headers={"Authorization": "Bearer owner"}).status_code == 503
