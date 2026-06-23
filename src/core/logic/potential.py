from __future__ import annotations
from typing import TYPE_CHECKING
from bitarray import bitarray
from decimal import Decimal

if TYPE_CHECKING:
    from .node import Node

class Potential:
    def __init__(self, a: Decimal = Decimal("1.0"), b: Decimal = Decimal("0.0")) -> None:
        self.a: Decimal = a
        self.b: Decimal = b
        self.path: bitarray = bitarray()

    def reset(self) -> None:
        self.a = Decimal("1.0")
        self.b = Decimal("0.0")
        self.path = bitarray()
        
    def add_point(self, node_id: int) -> None:
        if len(self.path) <= node_id:
            self.path.extend([False] * (node_id - len(self.path) + 1))
        self.path[node_id] = True
    
    def get_copy_path(self) -> bitarray:
        return self.path.copy()

    def __lt__(self, other: Potential) -> bool:
        return (self.a, self.b) < (other.a, other.b)

    def __le__(self, other: Potential) -> bool:
        return (self.a, self.b) <= (other.a, other.b)

    def __gt__(self, other: Potential) -> bool:
        return (self.a, self.b) > (other.a, other.b)

    def __ge__(self, other: Potential) -> bool:
        return (self.a, self.b) >= (other.a, other.b)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Potential):
            return NotImplemented
        return self.a == other.a and self.b == other.b

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Potential):
            return NotImplemented
        return self.a != other.a or self.b != other.b

    def __str__(self) -> str:
        return f"Potential(a={self.a:.6f}, b={self.b:.6f})"

    def __repr__(self) -> str:
        return f"Potential(a={self.a}, b={self.b}, source=None)"