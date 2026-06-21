from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Protocol

if TYPE_CHECKING:
    from src.core.entities import Deal, Coin, Exchange

class IAnalyst(Protocol):
    async def get_best_deal(self, coin: Coin, exchange: Exchange) -> Deal: ...