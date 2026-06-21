from dataclasses import dataclass
from decimal import Decimal

from .coin import Coin

@dataclass
class Asset:
    coin: "Coin"
    ammount: Decimal