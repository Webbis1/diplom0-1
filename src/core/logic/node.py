from __future__ import annotations
from typing import TYPE_CHECKING
from decimal import Decimal

from .potential import Potential
if TYPE_CHECKING:
    from .edge import Edge


#Вершина
class Node:
    __slots__ = ("__price_to_usdt", "__potential", "__incoming_edges", "__outgoing_edges", "__id")
    
    def __init__(self, price_to_usdt: Decimal, id: int) -> None:
        self.__price_to_usdt: Decimal = price_to_usdt
        self.__potential: Potential = Potential()
        self.__incoming_edges: list[Edge] = []
        """Входящие ребра"""
        self.__outgoing_edges: list[Edge] = []
        """Исходящие ребра"""
        self.__id: int = id
        
    def get_id(self) -> int:
        return self.__id

    def add_incoming_edge(self, edge: Edge) -> None: 
        """Добавляет входящее ребро"""
        self.__incoming_edges.append(edge)
        # create_task(self.analyst._submit(f"edge_{id(edge)}", edge.recalculation_benefit_async))

    def get_outgoing_edges(self) -> list[Edge]:
        return self.__outgoing_edges
    
    def add_outgoing_edge(self, edge: Edge) -> None:
        """Добавляет исходящее ребро"""
        self.__outgoing_edges.append(edge)
        # self.update()

    def update(self) -> None | list[Edge]:
        if not self.__outgoing_edges:
            return
        best_edge: Edge = max(self.__outgoing_edges)

        if best_edge.get_potential() != self.__potential:
            if best_edge.get_potential().a <= 1.0:
                self.__potential.reset()
            else:
                self.__potential.a = best_edge.get_potential().a
                self.__potential.b = best_edge.get_potential().b
                
                self.__potential.path = best_edge.get_potential().get_copy_path()
                self.__potential.add_point(self.__id)

            return self.__incoming_edges

    def get_potential(self) -> Potential:
        return self.__potential
    
    def get_price(self) -> Decimal:
        return self.__price_to_usdt
    
    def update_price(self, new_price: Decimal):
        self.__price_to_usdt = new_price
    
    
    def __hash__(self) -> int:
        return hash(self.__id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self.__id == other.__id