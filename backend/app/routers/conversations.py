from fastapi import APIRouter, Depends, Query, Response
from ..core.auth import require_owner
from ..core.dependencies import get_services
from ..schemas.conversations import ConversationInput
from ..schemas.stocks import Symbol

router = APIRouter(prefix="/api/conversations", tags=["대화"])


@router.post("", status_code=201)
def create(payload: ConversationInput, uid=Depends(require_owner), services=Depends(get_services)):
    return services.conversations.create(uid, payload.symbol, payload.messages)


@router.get("")
def list_conversations(symbol: Symbol, cursor: str | None = Query(None, max_length=512), limit: int = Query(30, ge=1, le=100), uid=Depends(require_owner), services=Depends(get_services)):
    return services.conversations.list(uid, symbol, cursor, limit)


@router.get("/{id}")
def detail(id: str, uid=Depends(require_owner), services=Depends(get_services)):
    return services.conversations.get(uid, id)


@router.delete("/{id}", status_code=204)
def delete(id: str, uid=Depends(require_owner), services=Depends(get_services)):
    services.conversations.delete(uid, id)
    return Response(status_code=204)
