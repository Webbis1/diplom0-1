import asyncio

from abc import ABC, abstractmethod
from decimal import Decimal
import logging
from typing import AsyncIterator
from ccxt.pro import Exchange as CcxtProExchange


from src.application.interfaces import IExchange, Connection as IConnection, Api
from src.core.entities import Exchange as ExchangeModel, Asset, Coin, Ticker
from src.core.entities.market_info import MarketInfo

class Exchange(ABC, ExchangeModel):
    def __init__(self, name: str, conn: "IConnection") -> None:
        super().__init__(name, {})
        self.__balance_sub: list[asyncio.Queue["Asset"]] = []
        self.__price_sub: list[asyncio.Queue["Ticker"]] = []
        self.conn: "IConnection" = conn
    
    @property
    def logger(self):
        return logging.getLogger(f'BaseExchange for {self.name}')
      
    def subscribe_balance(self, coins: set["Coin"]) -> AsyncIterator["Asset"]:
        q: asyncio.Queue["Asset"] = asyncio.Queue(maxsize=100)
        self.__balance_sub.append(q)

        async def generator() -> AsyncIterator["Asset"]:
            try:
                while self.working:
                    asset: "Asset" = await q.get()
                    if asset.coin in coins:
                        yield asset
            finally:
                self.__balance_sub.remove(q)

        return generator()
            
    def subscribe_price(self, coins: set["Coin"]) -> AsyncIterator["Ticker"]:
        q: asyncio.Queue["Ticker"] = asyncio.Queue(maxsize=100)
        self.__price_sub.append(q)
        
        async def generator() -> AsyncIterator["Ticker"]:
            try:
                while self.working:
                    ticker: "Ticker" = await q.get()
                    if ticker.coin in coins:
                        yield ticker
            finally:
                self.__price_sub.remove(q)
        
        return generator()
            
    def _notify_balance_sub(self, coin: "Coin", new_ammount: Decimal):
        asset: "Asset" = Asset(coin, new_ammount)
        for sub in self.__balance_sub:
            try:
                sub.put_nowait(asset)
            except asyncio.QueueFull:
                sub.get_nowait()
                sub.put_nowait(asset)
            
    def _notify_price_sub(self, coin: "Coin", new_price: Decimal):
        ticker: "Ticker" = Ticker(coin, new_price)
        for sub in self.__price_sub:
            try:
                sub.put_nowait(ticker)
            except asyncio.QueueFull:
                sub.get_nowait()
                sub.put_nowait(ticker)
    
    
    @abstractmethod
    async def _balance_request(self, api: "Api"): ...
    @abstractmethod
    async def _price_request(self, api: "Api"): ...
                  
    async def run_balance_observer(self) -> None:
        await self._working.wait()
        while self.working:
            try:
                async with self.conn.client() as api:
                    if api is None:
                        await asyncio.sleep(1)
                        continue
                    
                    while self.conn.working and self.working:
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
                async with self.conn.client() as api:
                    if api is None:
                        await asyncio.sleep(1)
                        continue

                    while self.conn.working and self.working:
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
        
    @abstractmethod  
    async def get_markets(self) -> list[MarketInfo]: ...

                            
    async def launch(self, tg: asyncio.TaskGroup) -> None:
        tg.create_task(self.run_balance_observer())
        tg.create_task(self.run_price_observer())        
        self._working.set()



