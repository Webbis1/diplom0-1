from dataclasses import dataclass
from decimal import Decimal

from .coin import Coin


@dataclass(frozen=True, slots=True)
class MarketInfo:
    base: Coin
    quote: Coin
    taker_fee: Decimal
    min_amount: Decimal
    active: bool