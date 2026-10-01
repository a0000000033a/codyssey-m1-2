from uuid import uuid4
from .data import owned
from .paging import page
from .stocks import now
from ..core.errors import ApiError


class ConversationService:
    def __init__(self, repo, stocks):
        self.repo, self.stocks = repo, stocks

    def create(self, uid, symbol, messages):
        stock = self.stocks.require_stock(symbol)
        id, stamp = uuid4().hex, now()
        meta = {"owner_uid": uid, "market": "KR", "symbol": symbol, "stock_name": stock["name"],
                "title": messages[0].content[:40] if messages else "새 대화", "created_at": stamp,
                "updated_at": stamp, "status": "active", "message_count": len(messages)}
        def write(tx):
            tx.put("conversations", id, meta)
            for seq, message in enumerate(messages):
                tx.put(f"conversations/{id}/messages", str(seq).zfill(12), dict(message.model_dump(), owner_uid=uid, sequence=seq, turn_id="manual", created_at=stamp, context_snapshot=None))
        self.repo.atomic(write)
        return self.get(uid, id)

    def list(self, uid, symbol, cursor=None, limit=30):
        rows = self.repo.list("conversations", {"owner_uid": uid, "symbol": symbol})
        rows.sort(key=lambda x: (x["updated_at"], x["id"]), reverse=True)
        for row in rows:
            row.pop("pending", None)
        return page(rows, cursor, limit, f"conversations:{uid}:{symbol}")

    def get(self, uid, id):
        row = owned(self.repo, "conversations", uid, id)
        messages = sorted(self.repo.list(f"conversations/{id}/messages"), key=lambda x: x["sequence"])
        row.pop("pending", None)
        return dict(row, messages=messages)

    def delete(self, uid, id):
        def mark(tx):
            row = owned(tx, "conversations", uid, id)
            row.pop("id", None)
            row["status"] = "deleting"
            tx.put("conversations", id, row)
        self.repo.atomic(mark)
        try:
            for request in self.repo.list("chat_requests", {"owner_uid": uid, "conversation_id": id}):
                # Keep only a tombstone to reject late retries; erase answer/context copies.
                key = request.pop("id")
                tombstone = {k: request[k] for k in ("owner_uid", "conversation_id", "fingerprint")}
                tombstone["status"] = "deleted"
                self.repo.put("chat_requests", key, tombstone)
            for message in self.repo.list(f"conversations/{id}/messages"):
                self.repo.delete(f"conversations/{id}/messages", message["id"])
            self.repo.delete("conversations", id)
        except Exception:
            raise ApiError(503, "delete_incomplete", "삭제를 완료하지 못했습니다. 다시 삭제해주세요.") from None
