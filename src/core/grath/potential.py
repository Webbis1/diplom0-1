from __future__ import annotations
from typing import TYPE_CHECKING
from bitarray import bitarray

if TYPE_CHECKING:
    from .node import Node

class Potential:
    def __init__(self, a: float = 1.0, b: float = 0.0) -> None:
        self.a: float = a
        self.b: float = b
        self.path: bitarray = bitarray()

    def reset(self) -> None:
        self.a = 1.0
        self.b = 0.0
        self.path = bitarray()
        
    def add_point(self, node_id: int):
        self.path[node_id] = 1
    
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