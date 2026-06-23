from __future__ import annotations
from asyncio import Queue, create_task, Event
from decimal import Decimal
from typing import TYPE_CHECKING

from src.core.utils.async_rlock import AsyncRLock

from .node import Node
from .edge import Edge
from src.core.dto.route_candidate import RouteCandidate

if TYPE_CHECKING:
    from ..entities import Coin
    from ..entities import Exchange
    from src.core.logic.potential import Potential
    from src.core.utils.async_rlock import AsyncRLock
    

class Graph:
    def __init__(self) -> None:
        self.nodes: dict[Coin, dict[Exchange, Node]] = {}
        self.edges: dict[Node, dict[Node, Edge]] = {}

        self._node_registry: set[Node] = set()
        self._edge_registry: set[Edge] = set()

        self.__update_queue: Queue[Node | Edge] = Queue()

        self._update_pending: set[Node | Edge] = set()

        self._working: Event = Event()
        
        self._route_lock: AsyncRLock = AsyncRLock()
        
    @property
    def working(self) -> bool:
        return self._working.is_set()

    async def ensure_node(self, coin: "Coin", ex: "Exchange", price: Decimal) -> "Node":
        if coin not in self.nodes:
            self.nodes[coin] = {}
            
        if ex not in self.nodes[coin]:
            node_id: int = len(self._node_registry)
            node: Node = Node(price, node_id)
            self.nodes[coin][ex] = node
            self._node_registry.add(node)
        else:
            node = self.nodes[coin][ex]
            node.update_price(price)
            
        for edge in node.get_outgoing_edges():
            await self.__put_updatable(edge)
            
        for edge in node.get_incoming_edges():
            await self.__put_updatable(edge)
            
        await self.__put_updatable(node)
        return node

    async def ensure_edge(self, departure: "Node", destination: "Node", commission: Decimal, fixed_fee: Decimal) -> "Edge":
        if departure not in self._node_registry or destination not in self._node_registry:
            raise KeyError("Node was not created via ensure_node")
        
        
        edge: Edge = self.edges.setdefault(departure, {}).setdefault(destination, Edge(departure, destination, commission, fixed_fee))
        
        if edge in self._edge_registry:
            edge.set_commission(commission)
            edge.set_fixed_fee(fixed_fee)
        else:
            self._edge_registry.add(edge)
        
        await self.__put_updatable(edge)
        
        return edge

    async def __put_updatable(self, updatable: Node | Edge) -> None:
        if updatable not in self._update_pending:
            self._update_pending.add(updatable)
            await self.__update_queue.put(updatable)

    async def __update_worker(self) -> None:
        await self._working.wait()
        while self._working.is_set():
            refreshable: Node | Edge | None = None
            try:
                refreshable = await self.__update_queue.get()
                if updatables := refreshable.update():
                    for updatable in updatables:
                        if updatable in self._edge_registry or updatable in self._node_registry:
                            await self.__put_updatable(updatable)
            finally:
                if refreshable is not None:
                    self._update_pending.discard(refreshable)
                    self.__update_queue.task_done()
    async def start(self) -> None:
        if self.working:
            return
        create_task(self.__update_worker())
        self._working.set()

    async def wait_completion(self) -> None:
        await self.__update_queue.join()
        
    async def stop(self):
        self._working.clear()
        
        