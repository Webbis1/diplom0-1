from __future__ import annotations

class Potential:
    def __init__(self, a: float = 1.0, b: float = 0.0) -> None:
        self.a: float = a
        self.b: float = b
        self.path: tuple[str, ...] = ()

    def reset(self) -> None:
        self.a = 1.0
        self.b = 0.0
        self.path = ()

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