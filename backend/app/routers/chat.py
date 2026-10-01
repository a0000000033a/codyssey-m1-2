from fastapi import APIRouter, Depends
from ..core.auth import require_owner
from ..core.dependencies import get_services
from ..schemas.chat import ChatInput

router = APIRouter(prefix="/api/chat", tags=["AI 채팅"])


@router.post("")
def chat(payload: ChatInput, uid=Depends(require_owner), services=Depends(get_services)):
    return services.chat.send(uid, payload)
