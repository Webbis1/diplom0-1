from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING

from .potential import Potential
if TYPE_CHECKING:
    from .node import Node

#Ребро
class Edge:
    def __init__(self, departure: Node, destination: Node, commission: Decimal, fixed_fee: Decimal = Decimal("0.0")) -> None:
        self.__departure: Node = departure  # Узел отправления
        self.__destination: Node = destination  # Узел назначения
        
        
        self.__commission: Decimal = 1 - commission
        self.__fixed_fee: Decimal = fixed_fee
        self.__potential: Potential = Potential()
        
        self.__departure.add_outgoing_edge(self)
        self.__destination.add_incoming_edge(self)
        
    @property
    def multiplier(self) -> Decimal:
        return self.__commission * (self.__destination.get_price() / self.__departure.get_price()) if self.__fixed_fee > 0 else self.__commission
    
    def update(self) -> list[Node] | None:
        potential: Potential = self.__destination.get_potential()

        departure_id: int = self.__departure.get_id()
        if len(potential.path) > departure_id and potential.path[departure_id]:
            self.__potential.reset()
            return

        self.__potential.a = potential.a * self.multiplier
        self.__potential.b = potential.b - (self.__fixed_fee * self.multiplier * potential.a)

        if self.__potential.a <= 1:
            self.__potential.reset()
        else:
            self.__potential.path = potential.get_copy_path()

        return [self.__departure]
        

    def set_commission(self, commission: Decimal) -> None:
        self.__commission = commission

    def set_fixed_fee(self, fixed_fee: Decimal) -> None:
        self.__fixed_fee = fixed_fee


    
    def get_fixed_fee(self) -> Decimal:
        return self.__fixed_fee
    
    def get_potential(self) -> Potential:
        return self.__potential
    
    def __hash__(self) -> int:
        return hash((self.__departure.get_id(), self.__destination.get_id()))

    
    def __lt__(self, other: Edge) -> bool:
        return self.__potential < other.__potential

    def __le__(self, other: Edge) -> bool:
        return self.__potential <= other.__potential

    def __gt__(self, other: Edge) -> bool:
        return self.__potential > other.__potential

    def __ge__(self, other: Edge) -> bool:
        return self.__potential >= other.__potential

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return self.__potential == other.__potential

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return NotImplemented
        return self.__potential != other.__potential

