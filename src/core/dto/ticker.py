from dataclasses import dataclass
from decimal import Decimal
from ..entities.coin import Coin

@dataclass(frozen=True) 
class Ticker:
    coin: "Coin"
    price: Decimal