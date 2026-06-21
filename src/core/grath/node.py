from __future__ import annotations
from typing import TYPE_CHECKING
from asyncio import create_task

if TYPE_CHECKING:
    from .potential import Potential
    from .edge import Edge

class Node:
    def __init__(self, exchange_id: int, coin_id: int, price_to_usdt: float = 1.0) -> None:
        self.exchange_id: int = exchange_id
        self.coin_id: int = coin_id
        self.id: str = f"{self.exchange_id}_{self.coin_id}"
        self.price_to_usdt: float = price_to_usdt
        self.potential: Potential = Potential()
        self.incoming_edges: list[Edge] = []
        self.outgoing_edges: list[Edge] = []
        self.analyst = Analyst()

    def add_incoming_edge(self, edge: Edge) -> None:
        self.incoming_edges.append(edge)
        create_task(self.analyst._submit(f"edge_{id(edge)}", edge.recalculation_benefit_async))

    def add_outgoing_edge(self, edge: Edge) -> None:
        self.outgoing_edges.append(edge)
        self.update()

    def update(self) -> None:
        if not self.outgoing_edges:
            return
        best_edge: Edge = max(self.outgoing_edges)

        if best_edge.potential != self.potential:
            if best_edge.potential.a <= 1.0:
                self.potential.reset()
            else:
                self.potential.a = best_edge.potential.a
                self.potential.b = best_edge.potential.b
                self.potential.path = best_edge.potential.path + (self.id,)

            self._notify_ancestors()

    def _notify_ancestors(self) -> None:
        for edge in self.incoming_edges:
            create_task(self.analyst._submit(f"edge_{id(edge)}", edge.recalculation_benefit_async))
