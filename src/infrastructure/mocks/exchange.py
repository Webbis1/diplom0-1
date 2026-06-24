import asyncio
import logging
from decimal import Decimal
from typing import AsyncIterator, Any

from src.core.dto import Asset, Ticker, MarketInfo
from src.core.entities import Coin, Exchange as ExchangeModel
from src.application.interfaces import Api, Connection as IConnection
from ..base import Exchange as BaseExchange

# src/infrastructure/mocks/exchange.py
import asyncio
import logging
from decimal import Decimal
from typing import AsyncIterator, Any

from src.core.dto import Asset, Ticker, MarketInfo
from src.core.entities import Coin, Exchange as ExchangeModel
from src.application.interfaces import Api, Connection as IConnection
from ..base import Exchange as BaseExchange


class MockExchange(BaseExchange):

    def __init__(self, info: ExchangeModel, conn: IConnection) -> None:
        super().__init__(info, conn)
        self._tracked_price_coins: set[Coin] = set()
        self._tracked_balance_coins: set[Coin] = set()

    @property
    def __logger(self) -> logging.Logger:
        return logging.getLogger(f'MockExchange for {self.name}')

    def subscribe_price(self, coins: set[Coin]) -> AsyncIterator[Ticker]:
        self._tracked_price_coins.update(coins)
        self.__logger.debug(f"Subscribe price: {[c.symbol for c in coins]}")
        return super().subscribe_price(coins)

    def subscribe_balance(self, coins: set[Coin]) -> AsyncIterator[Asset]:
        self._tracked_balance_coins.update(coins)
        self.__logger.debug(f"Subscribe balance: {[c.symbol for c in coins]}")
        return super().subscribe_balance(coins)

    async def _balance_request(self, api: Api) -> None:
        if not self._tracked_balance_coins:
            await asyncio.sleep(1)
            return
        
        response: dict[str, Any] = await api.watch_balance()
        free: dict[str, float] = response.get("free", {})
        for coin in self._tracked_balance_coins:
            amount: float = free.get(coin.symbol, 0.0)
            self.__logger.debug(f"Balance update for {coin.symbol}: {amount}")
            self._notify_balance_sub(coin, Decimal(str(amount)))

    async def _price_request(self, api: Api) -> None:
        if not self._tracked_price_coins:
            await asyncio.sleep(1)
            return
        
        for coin in self._tracked_price_coins:
            symbol: str = f"{coin.symbol}/USDT"
            response: dict[str, Any] = await api.watch_ticker(symbol)
            price: Decimal = Decimal(str(response.get("last", 0.0)))
            self.__logger.debug(f"Price update for {coin.symbol}: {price}")
            self._notify_price_sub(coin, price)

    async def get_markets(self) -> list[MarketInfo]:
        async with self._conn.client() as api:
            if api is None:
                return []
            
            try:
                raw_markets: list[dict[str, Any]] = await getattr(api, "fetch_markets")()
                markets: list[MarketInfo] = []
                
                for raw in raw_markets:
                    base_coin = Coin(
                        address=raw.get("base", "").lower(),
                        symbol=raw.get("base", "")
                    )
                    quote_coin = Coin(
                        address=raw.get("quote", "").lower(),
                        symbol=raw.get("quote", "")
                    )
                    
                    markets.append(MarketInfo(
                        base=base_coin,
                        quote=quote_coin,
                        taker_fee=Decimal(str(raw.get("taker", 0.001))),
                        min_amount=Decimal(str(raw.get("limits", {}).get("amount", {}).get("min", 0.5))),
                        active=raw.get("active", True)
                    ))
                
                return markets
            except Exception as e:
                self.logger.error(f"Failed to fetch markets: {e}")
                return []