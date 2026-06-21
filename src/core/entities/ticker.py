from dataclasses import dataclass
from decimal import Decimal
from .coin import Coin

@dataclass
class Ticker:
    coin: "Coin"
    price: Decimal