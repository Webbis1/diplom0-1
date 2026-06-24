from dataclasses import dataclass

@dataclass
class Coin:
    address: str
    symbol: str
    
    def __hash__(self) -> int:
        return hash(self.address)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Coin):
            return NotImplemented
        return self.address == other.address