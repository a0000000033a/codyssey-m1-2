from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .stocks import Symbol


class RecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: Symbol
    date: date
    value: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    memo: str = Field(default="", max_length=1000)

    @field_validator("date")
    @classmethod
    def past_or_today(cls, value):
        if value > datetime.now(ZoneInfo("Asia/Seoul")).date():
            raise ValueError("미래 날짜는 기록할 수 없습니다.")
        return value
