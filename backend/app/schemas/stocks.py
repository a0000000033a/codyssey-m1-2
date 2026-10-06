from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints

Symbol = Annotated[str, StringConstraints(pattern=r"^\d{6}$")]


class StockInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: Symbol
