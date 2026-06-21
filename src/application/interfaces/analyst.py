from typing import Protocol
from src.core.entities import Deal, Coin, Exchange

class IAnalyst(Protocol):
    async def get_best_deal(self, coin: "Coin", exchange: "Coin") -> "Deal": ...