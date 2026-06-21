from __future__ import annotations
from typing import TYPE_CHECKING
from asyncio import create_task
from decimal import Decimal

if TYPE_CHECKING:
    from .potential import Potential
    from .edge import Edge


#Вершина
class Node:
    def __init__(self, price_to_usdt: Decimal) -> None:
        self.__price_to_usdt: Decimal = price_to_usdt
        self.__potential: Potential = Potential()
        self.__incoming_edges: list[Edge] = []
        self.__outgoing_edges: list[Edge] = []
        self.__id = -1
    
    def set_id(self, id: int):
        self.__id = id
        
    def get_id(self) -> int:
        return self.__id

    def add_incoming_edge(self, edge: Edge) -> None: 
        """Добавляет входящее ребро"""
        self.__incoming_edges.append(edge)
        # create_task(self.analyst._submit(f"edge_{id(edge)}", edge.recalculation_benefit_async))

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