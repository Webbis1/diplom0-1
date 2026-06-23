from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Self

from src.core.dto.route_candidate import RouteCandidate
from src.core.utils.async_rlock import AsyncRLock
from src.core.logic import Graph

if TYPE_CHECKING:
    from src.core.logic import Edge, Node, Potential
    from .exchange import Exchange
    from src.core.entities import Ticker, Coin
    
import asyncio



class Analyst:
    __instance: Self | None = None

    def __new__(cls, *args, **kwargs) -> Self:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, ex_list: list[Exchange]) -> None:
        if hasattr(self, "_initialized"):
            return
        self._graph: Graph = Graph()
        self._route_lock: AsyncRLock = AsyncRLock()
        self.__exchanges: list[Exchange] = ex_list
        self._initialized: bool = True

    async def launch(self, tg: asyncio.TaskGroup) -> None:
        tg.create_task(self._graph.start())
        for ex in self.__exchanges:
            tg.create_task(self.__subscribe_to_exchange(ex))

    async def __subscribe_to_exchange(self, ex: Exchange) -> None:
        coins: set[Coin] = set()
        async for ticker in ex.subscribe_price(coins):
            await self._graph.ensure_node(ticker.coin, ex, ticker.price)
            
    async def get_optimal_route(self, coin: Coin, exchange: Exchange) -> RouteCandidate | None:
        async with self._route_lock:
            coin_nodes = self._graph.nodes.get(coin)
            if not coin_nodes:
                return None
                
            node = coin_nodes.get(exchange)
            if node is None:
                return None
            
            outgoing_edges: list[Edge] = node.get_outgoing_edges()
            if not outgoing_edges:
                return None
                
            best_edge: Edge | None = None
            best_potential: Potential | None = None
            
            for edge in outgoing_edges:
                edge_potential: Potential = edge.get_potential()
                if best_potential is None or edge_potential > best_potential:
                    best_potential = edge_potential
                    best_edge = edge
                    
            if best_edge is None or best_potential is None or best_potential.a <= Decimal("1.0"):
                return None
                
            destination_node: Node = best_edge.get_destination()
            
            return RouteCandidate(
                departure=node,
                destination=destination_node,
                edge=best_edge,
                multiplier=best_potential.a,
                residual_value=best_potential.b,
                path=best_potential.get_copy_path()
            )