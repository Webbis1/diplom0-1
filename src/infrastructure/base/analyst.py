from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Self

from src.core.logic import Graph

if TYPE_CHECKING:
    from .exchange import Exchange
    from src.core.entities import Ticker, Coin


class Analyst:
    __instance: Self | None = None

    def __new__(cls, *args, **kwargs) -> Self:
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, ex_list: list[Exchange]) -> None:
        if hasattr(self, "_initialized"):
            return
        self.__graph: Graph = Graph()
        self.__exchanges: list[Exchange] = ex_list
        self._initialized: bool = True

    async def launch(self, tg: asyncio.TaskGroup) -> None:
        tg.create_task(self.__graph.start())
        for ex in self.__exchanges:
            tg.create_task(self.__subscribe_to_exchange(ex))

    async def __subscribe_to_exchange(self, ex: Exchange) -> None:
        coins: set[Coin] = set()
        async for ticker in ex.subscribe_price(coins):
            await self.__graph.ensure_node(ticker.coin, ex, ticker.price)