from __future__ import annotations
from decimal import Decimal
from typing import TYPE_CHECKING
from typing import Dict, Tuple
from unicodedata import decimal

if TYPE_CHECKING:
    from .node import Node
    from .edge import Edge
    from ..entities import Coin
    from ..entities import Exchange
    from .async_unic_queue import AsyncUnicQueue
    
    
class Graph:
    def __init__(self) -> None:
        self.nodes: dict[Coin, dict[Exchange, Node]] = {}
        self.edges: dict[Node, dict[Node, Edge]] = {}
        
        self.__node_registry: set[Node] = set()
        self.__edge_registry: set[Edge] = set()
        
        self.__node_update_q: AsyncUnicQueue[Node] = AsyncUnicQueue()
        self.__edge_update_q: AsyncUnicQueue[Edge] = AsyncUnicQueue()
        
        
    def ensure_node(self, coin: Coin, ex: Exchange, price: Decimal) -> Node:
        node: Node = self.nodes.setdefault(coin, {}).setdefault(ex, Node(price))
        if node not in self.__node_registry:
            node_id: int = len(self.__node_registry)
            node.set_id(node_id)
            self.__node_registry.add(node)
        return node

    def ensure_edge(self, departure: Node, destination: Node, multiplier: float, fixed_fee: float) -> Edge:
        if departure not in self.__node_registry or destination not in self.__node_registry:
            raise KeyError("Node was not created via ensure_node")
        
        edge: Edge = self.edges.setdefault(departure, {}).setdefault(destination, Edge(departure, destination, multiplier, fixed_fee))
        self.__edge_registry.add(edge)
        return edge
    
    async def __edge_worker(self):
        while True:
            try:
                edge: Edge = await self.__edge_update_q.get()
                if node := edge.recalculation_benefit():
                    if node in self.__node_registry:
                        await self.__node_update_q.put(node)
            finally:
                self.__edge_update_q.task_done()
                
    async def __node_worker(self):
        while True:
            try:
                node: Node = await self.__node_update_q.get()
                if edges := node.update():
                    for edge in edges:
                        if edge in self.__edge_registry:
                            await self.__edge_update_q.put(edge)
            finally:
                self.__node_update_q.task_done()