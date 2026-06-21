from asyncio import Event
from dataclasses import dataclass
from .coin import Coin

@dataclass
class Exchange:
    name: str
    address_list: dict[str, "Coin"]
    _working: Event = Event()
    
    @property
    def working(self) -> bool:
        return self._working.is_set()