from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .stocks import Symbol


class ManualMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ConversationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: Symbol
    messages: list[ManualMessage] = Field(default_factory=list, max_length=100)
