"""Lazy construction of external adapters; HTTP imports never contact providers."""
from threading import Lock
from types import SimpleNamespace
from fastapi import Request

from .auth import firebase_app
from .errors import ApiError

_services_lock = Lock()


def get_services(request: Request):
    with _services_lock:
        if request.app.state.dependencies is None:
            from firebase_admin import firestore
            from ..repositories.firestore import FirestoreRepository
            from ..providers.market import MarketProvider
            from ..services.stocks import StockService
            from ..services.data import DataService
            from ..services.summary import SummaryService
            from ..services.conversations import ConversationService
            from ..services.chat import ChatService
            from ..providers.ai import AIProvider
            try:
                repo = FirestoreRepository(firestore.client(app=firebase_app(request.app.state.settings)))
                stocks = StockService(repo, MarketProvider())
                request.app.state.dependencies = SimpleNamespace(repo=repo, stocks=stocks, data=DataService(repo, stocks), summary=SummaryService(repo, stocks), conversations=ConversationService(repo, stocks))
                services = request.app.state.dependencies
                services.chat = ChatService(repo, services.summary, services.conversations, AIProvider(request.app.state.settings), request.app.state.settings)
            except ApiError:
                raise
            except Exception:
                raise ApiError(503, "storage_unavailable", "저장소 연결 설정을 확인해주세요.") from None
        return request.app.state.dependencies
