"""Fenced Firestore transactions for request deduplication and durable turns."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from uuid import uuid4
from .data import owned
from .stocks import now
from ..core.errors import ApiError


class TurnStore:
    def __init__(self, repo):
        self.repo = repo

    def acquire_turn(self, uid, payload, lease_seconds, stock_name):
        key = hashlib.sha256(f"{uid}:{payload.request_id}".encode()).hexdigest()
        fingerprint = hashlib.sha256(json.dumps(payload.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()
        token, proposed_id = uuid4().hex, uuid4().hex
        def acquire(tx):
            previous = tx.get("chat_requests", key)
            if previous and previous["fingerprint"] != fingerprint:
                raise ApiError(409, "request_conflict", "이미 사용한 요청 ID입니다.")
            id = previous["conversation_id"] if previous else payload.conversation_id or proposed_id
            row = tx.get("conversations", id)
            if previous or payload.conversation_id:
                row = owned(tx, "conversations", uid, id)
                row.pop("id", None)
            else:
                stamp = now()
                row = {"owner_uid": uid, "market": "KR", "symbol": payload.symbol, "stock_name": stock_name,
                       "title": payload.message[:40], "created_at": stamp, "updated_at": stamp, "status": "active", "message_count": 0}
            if row["symbol"] != payload.symbol:
                raise ApiError(400, "symbol_mismatch", "대화에 연결된 종목과 다릅니다.")
            if row["status"] != "active":
                raise ApiError(409, "conversation_deleting", "삭제 중인 대화에는 질문할 수 없습니다.")
            if previous and previous["status"] == "complete":
                return {"result": previous["result"]}
            if previous and previous["status"] == "uncertain":
                raise ApiError(409, "save_uncertain", "답변 저장을 확인하지 못했습니다. 대화를 다시 불러와 확인해주세요.")
            pending = row.get("pending")
            if pending and datetime.fromisoformat(pending["lease_until"]) > datetime.now(timezone.utc):
                raise ApiError(409, "turn_pending", "이 대화의 답변을 처리 중입니다. 잠시 후 다시 확인해주세요.")
            row["pending"] = {"request_key": key, "token": token, "lease_until": (datetime.now(timezone.utc)+timedelta(seconds=lease_seconds)).isoformat()}
            request = {"owner_uid": uid, "conversation_id": id, "fingerprint": fingerprint, "status": "processing", "token": token}
            tx.put("conversations", id, row)
            tx.put("chat_requests", key, request)
            return {"key": key, "token": token, "conversation_id": id, "uid": uid}
        return self.repo.atomic(acquire)

    def commit_turn(self, claim, question, answer, context):
        def commit(tx):
            request = tx.get("chat_requests", claim["key"])
            row = owned(tx, "conversations", claim["uid"], claim["conversation_id"])
            row.pop("id", None)
            if request["token"] != claim["token"] or row.get("pending", {}).get("token") != claim["token"]:
                raise ApiError(409, "turn_replaced", "이전 요청의 처리 시간이 만료되었습니다. 대화를 다시 불러와주세요.")
            if row["status"] != "active":
                raise ApiError(409, "conversation_deleting", "대화가 삭제 중입니다.")
            stamp, sequence = now(), row["message_count"]
            user = {"role": "user", "content": question, "sequence": sequence, "turn_id": claim["key"], "created_at": stamp, "context_snapshot": None}
            assistant = {"role": "assistant", "content": answer, "sequence": sequence+1, "turn_id": claim["key"], "created_at": stamp, "context_snapshot": context}
            collection = f"conversations/{claim['conversation_id']}/messages"
            tx.put(collection, str(sequence).zfill(12), dict(user, owner_uid=claim["uid"]))
            tx.put(collection, str(sequence+1).zfill(12), dict(assistant, owner_uid=claim["uid"]))
            if row["message_count"] == 0:
                row["title"] = question[:40]
            row.update(message_count=sequence+2, updated_at=stamp)
            row.pop("pending", None)
            result = {"conversation_id": claim["conversation_id"], "user_message": user, "assistant_message": assistant, "context": context}
            request.update(status="complete", result=result)
            tx.put("conversations", claim["conversation_id"], row)
            tx.put("chat_requests", claim["key"], request)
            return result
        return self.repo.atomic(commit)

    def release(self, claim, status="failed"):
        def release(tx):
            request = tx.get("chat_requests", claim["key"])
            row = tx.get("conversations", claim["conversation_id"])
            if not request or request.get("token") != claim["token"]:
                return
            request["status"] = status
            if row and row.get("pending", {}).get("token") == claim["token"]:
                row.pop("pending", None)
                tx.put("conversations", claim["conversation_id"], row)
            tx.put("chat_requests", claim["key"], request)
        self.repo.atomic(release)
