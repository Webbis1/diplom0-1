from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.entities.coin import Coin


@dataclass(frozen=True)
class Order:
    id: str
    type: Literal["buy", "sell", "transfer"]
    coin: "Coin"
    amount: Decimal
    price: Decimal | None
    fee: Decimal
    timestamp: datetime
    status: Literal["pending", "filled", "failed"]