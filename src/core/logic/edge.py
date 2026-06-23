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
    
    def calculate_potential(self, incoming_potential: Potential) -> Potential | None:
        departure_id: int = self.__departure.get_id()
        
        if len(incoming_potential.path) > departure_id and incoming_potential.path[departure_id]:
            self.__potential.reset()
            return None

        self.__potential.a = incoming_potential.a * self.multiplier
        self.__potential.b = incoming_potential.b - (self.__fixed_fee * self.multiplier * incoming_potential.a)

        if self.__potential.a <= Decimal("1.0"):
            self.__potential.reset()
            return None
            
        self.__potential.path = incoming_potential.get_copy_path()
        return self.__potential

    def update(self) -> list[Node] | None:
        destination_potential: Potential = self.__destination.get_potential()
        updated_potential: Potential | None = self.calculate_potential(destination_potential)
        
        if updated_potential is None:
            return None
            
        return [self.__departure]

    def set_commission(self, commission: Decimal) -> None:
        self.__commission = commission

    def set_fixed_fee(self, fixed_fee: Decimal) -> None:
        self.__fixed_fee = fixed_fee

    def get_destination(self):
        return self.__destination
    
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

