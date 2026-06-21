from dataclasses import dataclass
from .coin import Coin
from .exchange import Exchange

@dataclass
class Deal:
    departure_coin: "Coin"
    departure_exchange: "Exchange"
    
    destination_coin: "Coin"
    destination_exchange: "Exchange"
    