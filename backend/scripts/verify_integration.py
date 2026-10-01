"""Explicit real-service smoke check. Reads a short-lived Firebase token from env."""
import json
import os
from uuid import uuid4
import httpx
from dotenv import load_dotenv

load_dotenv("backend/.env")
base = os.environ.get("VERIFY_API_BASE_URL", "http://127.0.0.1:8000")
token = os.environ.get("VERIFY_FIREBASE_ID_TOKEN", "")
if not token:
    print(json.dumps({"status": "not_run", "reason": "VERIFY_FIREBASE_ID_TOKEN is required"}))
    raise SystemExit(2)
created_records, created_conversations = [], []
checks = []
try:
    with httpx.Client(base_url=base, headers={"Authorization": "Bearer " + token}, timeout=100) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json() if response.status_code != 204 else None
        request("GET", "/api/me")
        summary = request("GET", "/api/data/summary?symbol=005930")
        assert summary["market_data"]["count"] >= 100
        checks.append("real_stored_market_summary")
        body = {"symbol": "005930", "date": summary["market_data"]["end"], "value": 12345, "memo": "integration smoke check"}
        record = request("POST", "/api/data", json=body); created_records.append(record["id"])
        changed = request("PUT", f"/api/data/{record['id']}", json=dict(body, value=12346))
        assert changed["value"] == 12346
        checks.append("record_create_update")
        for _ in range(2):
            conversation = request("POST", "/api/conversations", json={"symbol": "005930", "messages": []})
            created_conversations.append(conversation["id"])
        assert created_conversations[0] != created_conversations[1]
        if os.environ.get("VERIFY_CALL_AI") == "1":
            chat = {"symbol": "005930", "conversation_id": created_conversations[0], "request_id": str(uuid4()), "message": "저장된 데이터 기간과 평균 종가를 간단히 설명해주세요."}
            first = request("POST", "/api/chat", json=chat)
            repeated = request("POST", "/api/chat", json=chat)
            assert first == repeated
            messages = request("GET", f"/api/conversations/{created_conversations[0]}")["messages"]
            assert len(messages) == 2
            checks.append("real_ai_answer_and_idempotent_replay")
        else:
            checks.append("ai_not_run")
        print(json.dumps({"status": "passed", "count": summary["market_data"]["count"], "checks": checks}, ensure_ascii=False))
except Exception as exc:
    # Never print exception text, headers, credentials, responses or private bodies.
    print(json.dumps({"status": "failed", "error_type": type(exc).__name__, "checks": checks}))
    raise SystemExit(1) from None
finally:
    with httpx.Client(base_url=base, headers={"Authorization": "Bearer " + token}, timeout=60) as client:
        cleanup_ok = True
        for path, ids in [("data", created_records), ("conversations", created_conversations)]:
            for id in ids:
                try:
                    response = client.delete(f"/api/{path}/{id}")
                    cleanup_ok &= response.status_code in (204, 404)
                except Exception:
                    cleanup_ok = False
        print(json.dumps({"cleanup": "passed" if cleanup_ok else "incomplete"}))
