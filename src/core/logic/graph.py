from __future__ import annotations
from asyncio import Queue, create_task, Event
from decimal import Decimal
from typing import TYPE_CHECKING

from .node import Node
from .edge import Edge

if TYPE_CHECKING:
    from ..entities import Coin
    from ..entities import Exchange


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[Coin, dict[Exchange, Node]] = {}
        self.edges: dict[Node, dict[Node, Edge]] = {}

        self.__node_registry: set[Node] = set()
        self.__edge_registry: set[Edge] = set()

        self.__update_queue: Queue[Node | Edge] = Queue()

        self.__update_pending: set[Node | Edge] = set()

        self.__working: Event = Event()
        
    @property
    def working(self) -> bool:
        return self.__working.is_set()

    async def ensure_node(self, coin: "Coin", ex: "Exchange", price: Decimal) -> "Node":
        if coin not in self.nodes:
            self.nodes[coin] = {}
        if ex not in self.nodes[coin]:
            node_id: int = len(self.__node_registry)
            node: Node = Node(price, node_id)
            self.nodes[coin][ex] = node
            self.__node_registry.add(node)
        else: 
            node: Node = self.nodes[coin][ex]
            node.update_price(price)

        for edge in node.__outgoing_edges:
            await self.__put_updatable(edge)
        
        await self.__put_updatable(node)
         
        return node

    def ensure_edge(self, departure: "Node", destination: "Node", commission: Decimal, fixed_fee: Decimal) -> "Edge":
        if departure not in self.__node_registry or destination not in self.__node_registry:
            raise KeyError("Node was not created via ensure_node")

        edge: Edge = self.edges.setdefault(departure, {}).setdefault(destination, Edge(departure, destination, commission, fixed_fee))
        self.__edge_registry.add(edge)
        return edge

    async def __put_updatable(self, updatable: Node | Edge) -> None:
        if updatable not in self.__update_pending:
            self.__update_pending.add(updatable)
            await self.__update_queue.put(updatable)

    async def __update_worker(self) -> None:
        await self.__working.wait()
        while self.working:
            try:
                refreshable: Node | Edge = await self.__update_queue.get()
                if updatables := refreshable.update():
                    for updatable in updatables:
                        if updatable in self.__edge_registry or updatable in self.__node_registry:
                            await self.__put_updatable(updatable)
            finally:
                self.__update_pending.discard(refreshable)
                self.__update_queue.task_done()

    async def start(self) -> None:
        create_task(self.__update_worker())
        self.__working.set()

    async def wait_completion(self) -> None:
        await self.__update_queue.join()
        
    async def stop(self):
        self.__working.clear()