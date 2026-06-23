from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import TYPE_CHECKING, Self

from src.core.dto.route_candidate import RouteCandidate

from src.core.logic import Graph
from src.core.utils.async_rlock import AsyncRLock

if TYPE_CHECKING:
    from src.core.entities import Coin, Ticker
    from src.core.logic import Edge, Node, Potential
    from src.infrastructure.base.exchange import Exchange


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
        self._exchanges: list[Exchange] = ex_list
        self._initialized: bool = True

    async def launch(self, tg: asyncio.TaskGroup) -> None:
        tg.create_task(self._graph.start())
        await self._build_topology()
        for ex in self._exchanges:
            tg.create_task(self._subscribe_to_exchange(ex))

    async def stop(self) -> None:
        await self._graph.stop()

# Переименовать в src/infrastructure/base/analyst.py
    async def _build_topology(self) -> None:
        available_coins: dict[Coin, list[Exchange]] = {}
        
        for ex in self._exchanges:
            coins = await ex.get_available_coins()
            for coin in coins:
                if coin not in available_coins:
                    available_coins[coin] = []
                available_coins[coin].append(ex)
        
        for coin, exchanges in available_coins.items():
            if len(exchanges) < 2:
                continue
            
            nodes: dict[Exchange, Node] = {}
            for ex in exchanges:
                price = await ex.get_initial_price(coin)
                node = await self._graph.ensure_node(coin, ex, price)
                nodes[ex] = node
            
            for i, ex_a in enumerate(exchanges):
                for ex_b in exchanges[i + 1:]:
                    fee_a_to_b = await ex_a.get_withdrawal_fee(coin)
                    await self._graph.ensure_edge(
                        departure=nodes[ex_a],
                        destination=nodes[ex_b],
                        commission=Decimal("0.0"),
                        fixed_fee=fee_a_to_b
                    )
                    
                    fee_b_to_a = await ex_b.get_withdrawal_fee(coin)
                    await self._graph.ensure_edge(
                        departure=nodes[ex_b],
                        destination=nodes[ex_a],
                        commission=Decimal("0.0"),
                        fixed_fee=fee_b_to_a
                    )
        
        for ex in self._exchanges:
            usdt = ex.get_usdt()
            coins = available_coins.keys()
            
            for coin in coins:
                if coin == usdt:
                    continue
                
                if usdt not in self._graph.nodes or ex not in self._graph.nodes[usdt]:
                    continue
                if coin not in self._graph.nodes or ex not in self._graph.nodes[coin]:
                    continue
                
                usdt_node = self._graph.nodes[usdt][ex]
                coin_node = self._graph.nodes[coin][ex]
                
                fee = await ex.get_trading_fee(coin, usdt)
                
                await self._graph.ensure_edge(
                    departure=coin_node,
                    destination=usdt_node,
                    commission=fee,
                    fixed_fee=Decimal("0.0")
                )
                
                await self._graph.ensure_edge(
                    departure=usdt_node,
                    destination=coin_node,
                    commission=fee,
                    fixed_fee=Decimal("0.0")
                )
                
    async def _subscribe_to_exchange(self, ex: Exchange) -> None:
        coins: set[Coin] = set()
        for coin, exchanges in self._graph.nodes.items():
            if ex in exchanges:
                coins.add(coin)
        
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