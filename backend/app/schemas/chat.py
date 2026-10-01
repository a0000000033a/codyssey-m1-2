from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .stocks import Symbol


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: Symbol
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, pattern=r"^[a-zA-Z0-9_-]{1,128}$")
    request_id: UUID

    @field_validator("message")
    @classmethod
    def nonempty(cls, text):
        if not text.strip():
            raise ValueError("질문을 입력해주세요.")
        return text.strip()
