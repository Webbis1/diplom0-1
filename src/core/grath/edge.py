from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .potential import Potential
    from .node import Node

class Edge:
    def __init__(self, departure: Node, destination: Node, multiplier: float, fixed_fee: float = 0.0) -> None:
        self.departure: Node = departure
        self.destination: Node = destination
        self.multiplier: float = multiplier
        self.fixed_fee: float = fixed_fee
        self.potential: Potential = Potential()

    def recalculation_benefit(self) -> None:
        potential: Potential = self.destination.potential

        if self.departure.id in potential.path:
            self.potential.reset()
            return

        self.potential.a = potential.a * self.multiplier
        self.potential.b = potential.b - (self.fixed_fee * self.multiplier * potential.a)

        if self.potential.a <= 1:
            self.potential.reset()
        else:
            self.potential.path = potential.path

        self.departure.update()
        
    async def recalculation_benefit_async(self) -> None:
        self.recalculation_benefit()

    def update(self, multiplier: float, fixed_fee: float = 0.0) -> None:
        self.multiplier = multiplier
        self.fixed_fee = fixed_fee
        self.recalculation_benefit()

    def __lt__(self, other: Edge) -> bool:
        return self.potential < other.potential

    def __le__(self, other: Edge) -> bool:
        return self.potential <= other.potential

    def __gt__(self, other: Edge) -> bool:
        return self.potential > other.potential

    def __ge__(self, other: Edge) -> bool:
        return self.potential >= other.potential

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return self.potential == other.potential

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return self.potential != other.potential

