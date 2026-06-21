from __future__ import annotations
from asyncio import Queue, create_task, Event
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .node import Node
    from .edge import Edge
    from ..entities import Coin
    from ..entities import Exchange


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[Coin, dict[Exchange, Node]] = {}
        self.edges: dict[Node, dict[Node, Edge]] = {}

        self.__node_registry: set[Node] = set()
        self.__edge_registry: set[Edge] = set()

        self.__node_queue: Queue[Node] = Queue()
        self.__edge_queue: Queue[Edge] = Queue()
        
        self.__node_pending: set[Node] = set()
        self.__edge_pending: set[Edge] = set()
        
        self.__working: Event = Event()
        
    @property
    def working(self) -> bool:
        return self.__working.is_set()

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

    async def __put_node(self, node: Node) -> None:
        if node not in self.__node_pending:
            self.__node_pending.add(node)
            await self.__node_queue.put(node)

    async def __put_edge(self, edge: Edge) -> None:
        if edge not in self.__edge_pending:
            self.__edge_pending.add(edge)
            await self.__edge_queue.put(edge)

    async def __edge_worker(self) -> None:
        await self.__working.wait()
        while self.working:
            try:
                edge: Edge = await self.__edge_queue.get()
                if node := edge.recalculation_benefit():
                    if node in self.__node_registry:
                        await self.__put_node(node)
            finally:
                self.__edge_pending.discard(edge)
                self.__edge_queue.task_done()

    async def __node_worker(self) -> None:
        await self.__working.wait()
        while self.working:
            try:
                node: Node = await self.__node_queue.get()
                if edges := node.update():
                    for edge in edges:
                        if edge in self.__edge_registry:
                            await self.__put_edge(edge)
            finally:
                self.__node_pending.discard(node)
                self.__node_queue.task_done()

    async def start(self) -> None:
        create_task(self.__edge_worker())
        create_task(self.__node_worker())
        self.__working.set()

    async def wait_completion(self) -> None:
        await self.__node_queue.join()
        await self.__edge_queue.join()
        
    async def stop(self):
        self.__working.clear()