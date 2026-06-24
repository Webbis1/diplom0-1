import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
import logging
from typing import AsyncIterator, TYPE_CHECKING

from src.application.interfaces import IExchange, Api, Connection as IConnection
from src.core.entities import Exchange as ExchangeModel, Coin
from src.core.dto import Asset, Ticker, MarketInfo, Order


class Exchange(ABC):
    def __init__(self, info: ExchangeModel, conn: "IConnection") -> None:
        self.instance: ExchangeModel = info
        self._conn: "IConnection" = conn
        self._working = asyncio.Event()
        self._balance_sub: list[asyncio.Queue["Asset"]] = []
        self._price_sub: list[asyncio.Queue["Ticker"]] = []
    
    def get_instance(self) -> ExchangeModel:
        return self.instance
    
    @property
    def name(self) -> str:
        return self.instance.name
    
    @property
    def working(self) -> bool:
        return self._working.is_set()
    
    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(f'BaseExchange for {self.name}')
    
    def subscribe_balance(self, coins: set["Coin"]) -> AsyncIterator["Asset"]:
        q: asyncio.Queue["Asset"] = asyncio.Queue(maxsize=100)
        self._balance_sub.append(q)

        async def generator() -> AsyncIterator["Asset"]:
            try:
                await self._working.wait()
                while self.working:
                    asset: "Asset" = await q.get()
                    if asset.coin in coins:
                        yield asset
            finally:
                self._balance_sub.remove(q)

        return generator()
    
    def subscribe_price(self, coins: set["Coin"]) -> AsyncIterator["Ticker"]:
        q: asyncio.Queue["Ticker"] = asyncio.Queue(maxsize=100)
        self._price_sub.append(q)
        
        async def generator() -> AsyncIterator["Ticker"]:
            try:
                await self._working.wait()
                while self.working:
                    ticker: "Ticker" = await q.get()
                    if ticker.coin in coins:
                        yield ticker
            finally:
                self._price_sub.remove(q)
        
        return generator()
    
    def _notify_balance_sub(self, coin: "Coin", new_amount: Decimal) -> None:
        asset: "Asset" = Asset(coin, new_amount)
        for sub in self._balance_sub:
            try:
                sub.put_nowait(asset)
            except asyncio.QueueFull:
                sub.get_nowait()
                sub.put_nowait(asset)
    
    def _notify_price_sub(self, coin: "Coin", new_price: Decimal) -> None:
        ticker: "Ticker" = Ticker(coin, new_price)
        for sub in self._price_sub:
            try:
                sub.put_nowait(ticker)
            except asyncio.QueueFull:
                sub.get_nowait()
                sub.put_nowait(ticker)
    
    @abstractmethod
    async def _balance_request(self, api: "Api") -> None: ...
    
    @abstractmethod
    async def _price_request(self, api: "Api") -> None: ...
    
    @abstractmethod
    async def get_markets(self) -> list[MarketInfo]: ...
    
    async def run_balance_observer(self) -> None:
        await self._working.wait()
        while self.working:
            try:
                async with self._conn.client() as api:
                    if api is None:
                        await asyncio.sleep(1)
                        continue
                    
                    while self._conn.working and self.working:
                        try:
                            await self._balance_request(api)
                        except asyncio.CancelledError:
                            self.logger.warning("Принудительная остановка run_balance_observer")
                            raise
                        except Exception as e:
                            self.logger.error(f"Error during _balance_request: {type(e).__name__}: {e}")
                            break

            except asyncio.CancelledError:
                self.logger.info("balance observer task cancelled.")
                break
            except Exception as e:
                self.logger.critical(f"Unhandled error in balance observer loop: {type(e).__name__}: {e}")
                await asyncio.sleep(5)
    
    async def run_price_observer(self) -> None:
        await self._working.wait()
        while self.working:
            try:
                async with self._conn.client() as api:
                    if api is None:
                        await asyncio.sleep(1)
                        continue

                    while self._conn.working and self.working:
                        try:
                            await self._price_request(api)
                        except asyncio.CancelledError:
                            self.logger.warning("Принудительная остановка run_price_observer")
                            raise
                        except Exception as e:
                            self.logger.error(f"Error during _price_request: {type(e).__name__}: {e}")
                            break

            except asyncio.CancelledError:
                self.logger.info("Price observer task cancelled.")
                break
            except Exception as e:
                self.logger.critical(f"Unhandled error in price observer loop: {type(e).__name__}: {e}")
                await asyncio.sleep(5)
    
    async def launch(self, tg: asyncio.TaskGroup) -> None:
        tg.create_task(self.run_balance_observer())
        tg.create_task(self.run_price_observer())
        self._working.set()
    
    async def stop(self) -> None:
        self._working.clear()
    
    async def buy(self, asset: "Asset") -> "Order":
        async with self._conn.client() as api:
            if api is None:
                raise RuntimeError("API client is not available")
            
            symbol = f"{asset.coin.symbol}/USDT"
            response = await api.create_order(
                symbol=symbol,
                type="market",
                side="buy",
                amount=asset.amount,
                price=None
            )
            
            return Order(
                id=response.get("id", "unknown"),
                type="buy",
                coin=asset.coin,
                amount=Decimal(str(response.get("filled", 0))),
                price=Decimal(str(response.get("average", 0))),
                fee=Decimal(str(response.get("fee", {}).get("cost", 0))),
                timestamp=datetime.fromtimestamp(response.get("timestamp", 0) / 1000),
                status="filled" if response.get("status") == "closed" else "failed"
            )
    
    async def sell(self, asset: "Asset") -> "Order":
        async with self._conn.client() as api:
            if api is None:
                raise RuntimeError("API client is not available")
            
            symbol = f"{asset.coin.symbol}/USDT"
            response = await api.create_order(
                symbol=symbol,
                type="market",
                side="sell",
                amount=asset.amount,
                price=None
            )
            
            return Order(
                id=response.get("id", "unknown"),
                type="sell",
                coin=asset.coin,
                amount=Decimal(str(response.get("filled", 0))),
                price=Decimal(str(response.get("average", 0))),
                fee=Decimal(str(response.get("fee", {}).get("cost", 0))),
                timestamp=datetime.fromtimestamp(response.get("timestamp", 0) / 1000),
                status="filled" if response.get("status") == "closed" else "failed"
            )
    
    async def transfer(self, asset: "Asset", destination: "IExchange") -> "Order":
        async with self._conn.client() as api:
            if api is None:
                raise RuntimeError("API client is not available")
            
            address = await destination.get_deposit_address(asset.coin)
            if not address:
                raise ValueError(f"No deposit address available for {asset.coin.symbol} on destination exchange")
            
            response = await api.withdraw(
                symbol=asset.coin.symbol,
                amount=asset.amount,
                address=address
            )
            
            return Order(
                id=response.get("id", "unknown"),
                type="transfer",
                coin=asset.coin,
                amount=asset.amount,
                price=None,
                fee=Decimal(str(response.get("fee", {}).get("cost", 0))),
                timestamp=datetime.fromtimestamp(response.get("timestamp", 0) / 1000),
                status="pending" if response.get("status") == "pending" else "filled"
            )
            
            
    async def get_withdrawal_fee(self, coin: Coin) -> Decimal:
        async with self._conn.client() as api:
            if api is None:
                return Decimal("1.0")
            
            try:
                response = await api.fetch_withdrawal_fee(coin.symbol)
                return Decimal(str(response.get("withdraw", {}).get("fee", 1.0)))
            except Exception as e:
                self.logger.warning(f"Failed to fetch withdrawal fee for {coin.symbol}: {e}")
                return Decimal("1.0")
    
    async def get_available_coins(self) -> list[Coin]:
        async with self._conn.client() as api:
            if api is None:
                return []
            
            try:
                await api.load_markets()
                markets = await self.get_markets()
                coins = set()
                for market in markets:
                    coins.add(market.base)
                    coins.add(market.quote)
                return list(coins)
            except Exception as e:
                self.logger.error(f"Failed to fetch available coins: {e}")
                return []
    
    async def get_initial_price(self, coin: Coin) -> Decimal:
        async with self._conn.client() as api:
            if api is None:
                return Decimal("1.0")
            
            try:
                symbol = f"{coin.symbol}/USDT"
                response = await api.fetch_ticker(symbol)
                return Decimal(str(response.get("last", 1.0)))
            except Exception as e:
                self.logger.warning(f"Failed to fetch initial price for {coin.symbol}: {e}")
                return Decimal("1.0")
    
    async def get_trading_fee(self, base: Coin, quote: Coin) -> Decimal:
        async with self._conn.client() as api:
            if api is None:
                return Decimal("0.001")
            
            try:
                symbol = f"{base.symbol}/{quote.symbol}"
                response = await api.fetch_trading_fee(symbol)
                return Decimal(str(response.get("taker", 0.001)))
            except Exception as e:
                self.logger.warning(f"Failed to fetch trading fee for {base.symbol}/{quote.symbol}: {e}")
                return Decimal("0.001")
            
    async def get_deposit_address(self, coin: "Coin") -> str:
        async with self._conn.client() as api:
            if api is None:
                raise RuntimeError("API client is not available")
            
            response = await api.fetch_deposit_address(coin.symbol)
            return response.get("address", "")