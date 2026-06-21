from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .potential import Potential
    from .node import Node

#Ребро
class Edge:
    def __init__(self, departure: Node, destination: Node, multiplier: float, fixed_fee: float = 0.0) -> None:
        self.__departure: Node = departure  # Узел отправления
        self.__destination: Node = destination  # Узел назначения
        
        
        self.__multiplier: float = multiplier
        self.__fixed_fee: float = fixed_fee
        self.__potential: Potential = Potential()
        
        self.__departure.add_outgoing_edge(self)
        self.__destination.add_incoming_edge(self)
        

    def recalculation_benefit(self) -> Node | None:
        potential: Potential = self.__destination.get_potential()

        departure_id: int = self.__departure.get_id()
        if len(potential.path) > departure_id and potential.path[departure_id]:
            self.__potential.reset()
            return

        self.__potential.a = potential.a * self.__multiplier
        self.__potential.b = potential.b - (self.__fixed_fee * self.__multiplier * potential.a)

        if self.__potential.a <= 1:
            self.__potential.reset()
        else:
            self.__potential.path = potential.get_copy_path()

        return self.__departure
        
    async def recalculation_benefit_async(self) -> None:
        self.recalculation_benefit()

    def update(self, multiplier: float, fixed_fee: float = 0.0) -> None:
        self.__multiplier = multiplier
        self.__fixed_fee = fixed_fee
        self.recalculation_benefit()

    def get_multiplier(self) -> float:
        return self.__multiplier
    
    def get_fixed_fee(self) -> float:
        return self.__fixed_fee
    
    def get_potential(self) -> Potential:
        return self.__potential
    
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

