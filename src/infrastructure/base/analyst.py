from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING

from src.core.logic import Graph

if TYPE_CHECKING:
    from .exchange import Exchange
    from src.core.entities import Ticker, Coin

class Analyst:
    def __init__(self, ex_list: list[Exchange]):
        self.__graph: Graph = Graph()
        self.__exchanges: list[Exchange] = ex_list
        
    
    async def launch(self, tg: asyncio.TaskGroup):
        tg.create_task(self.__graph.start())
        for ex in self.__exchanges:
            tg.create_task(self.__subscribe_to_exchange(ex))
    
    async def __subscribe_to_exchange(self, ex: Exchange):
        coins: set[Coin] = set()
        async for ticker in ex.subscribe_price(coins):
            await self.__graph.ensure_node(ticker.coin, ex, ticker.price)
            