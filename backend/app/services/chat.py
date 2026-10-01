from .context import build_context
from .turns import TurnStore
from ..core.errors import ApiError


class ChatService:
    def __init__(self, repo, summary, conversations, ai, settings):
        self.summary, self.conversations, self.ai, self.settings = summary, conversations, ai, settings
        self.turns = TurnStore(repo)

    def send(self, uid, payload):
        if payload.conversation_id:
            conversation = self.conversations.get(uid, payload.conversation_id)
            if conversation["symbol"] != payload.symbol:
                raise ApiError(400, "symbol_mismatch", "대화에 연결된 종목과 다릅니다.")
        summary = self.summary.get(uid, payload.symbol)
        claim = self.turns.acquire_turn(uid, payload, self.settings.chat_lock_seconds, summary["stock"]["name"])
        if "result" in claim:
            return claim["result"]
        try:
            messages = self.conversations.get(uid, claim["conversation_id"])["messages"]
            context = build_context(summary, messages, self.settings.chat_input_max_chars, payload.message)
            answer = self.ai.answer(context)
        except Exception as exc:
            self.turns.release(claim)
            if isinstance(exc, ApiError):
                raise
            raise ApiError(502, "ai_unavailable", "AI 답변을 가져오지 못했습니다. 잠시 후 재시도해주세요.") from None
        try:
            return self.turns.commit_turn(claim, payload.message, answer, summary)
        except ApiError:
            raise
        except Exception:
            try:
                stored = self.turns.repo.get("chat_requests", claim["key"])
                if stored and stored["status"] == "complete":
                    return stored["result"]
                self.turns.release(claim, status="uncertain")
            except Exception:
                pass
            raise ApiError(503, "save_failed", "답변 저장을 확인하지 못했습니다. 대화를 다시 불러와 확인해주세요.") from None
