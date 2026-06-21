import asyncio
import logging
from typing import Any, Dict

class MockApi:
    def __init__(self):
        # Эмуляция словаря доступных методов (как в CCXT)
        self.has: Dict[str, bool] = {
            "watchTicker": True,
            "watchBalance": True,
            "fetchTicker": True,
            "fetchBalance": True,
        }
        
        # Сюда можно динамически передавать ошибку CCXT в тестах, 
        # чтобы проверить, как Connection её переваривает.
        self.exception_to_raise: Exception | None = None
        
        # Счётчики вызовов для ассертов в тестах
        self.load_markets_count = 0
        self.close_count = 0

    @property
    def logger(self):
        return logging.getLogger("MockApi")
    
    async def load_markets(self) -> None:
        self.load_markets_count += 1
        if self.exception_to_raise:
            raise self.exception_to_raise
        await asyncio.sleep(0.01)  # Имитация микро-задержки сети

    async def close(self) -> None:
        self.close_count += 1
        await asyncio.sleep(0.01)

    async def watch_ticker(self, symbol: str, params: dict[str, Any] = {}) -> dict[str, Any]:
        try:
            await asyncio.sleep(3)
            return {"symbol": symbol, "high": 100.0, "low": 95.0, "close": 97.5}
        except asyncio.CancelledError:
            self.logger.info("Cancel in watch_ticker")
            raise
        
    async def watch_balance(self, params: dict[str, Any] = {}) -> dict[str, Any]:
        try:
            await asyncio.sleep(2)
            return {"total": {"USDT": 1000.0}, "free": {"USDT": 1000.0}}
        except asyncio.CancelledError:
            self.logger.info("Cancel in watch_balance")
            raise
            
    async def fetch_ticker(self, symbol: str, params: dict[str, Any] = {}) -> dict[str, Any]:
        return {"symbol": symbol, "last": 97.5}

    async def fetch_balance(self, params: dict[str, Any] = {}) -> dict[str, Any]:
        return {"free": {"USDT": 1000.0}}