from dataclasses import dataclass
from decimal import Decimal

from ..entities.coin import Coin

@dataclass(frozen=True) 
class Asset:
    coin: "Coin"
    amount: Decimal