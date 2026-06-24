import asyncio
import logging
from typing import Any, Dict
from decimal import Decimal


class MockApi:
    def __init__(self):
        self.has: Dict[str, bool] = {
            "watchTicker": True,
            "watchBalance": True,
            "fetchTicker": True,
            "fetchBalance": True,
            "fetchWithdrawalFee": True,
            "fetchTradingFee": True,
            "fetchDepositAddress": True,
            "createOrder": True,
            "withdraw": True,
        }
        
        self.exception_to_raise: Exception | None = None
        
        self.load_markets_count = 0
        self.close_count = 0
        self.create_order_count = 0
        self.withdraw_count = 0

    @property
    def logger(self):
        return logging.getLogger("MockApi")
    
    async def load_markets(self) -> None:
        self.load_markets_count += 1
        if self.exception_to_raise:
            raise self.exception_to_raise
        await asyncio.sleep(0.01)

    async def close(self) -> None:
        self.close_count += 1
        await asyncio.sleep(0.01)

    async def watch_ticker(self, symbol: str, params: dict[str, Any] = {}) -> dict[str, Any]:
        try:
            await asyncio.sleep(3)
            return {"symbol": symbol, "high": 100.0, "low": 95.0, "close": 97.5, "last": 97.5}
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
        if self.exception_to_raise:
            raise self.exception_to_raise
        return {"symbol": symbol, "last": 97.5}

    async def fetch_balance(self, params: dict[str, Any] = {}) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        return {"free": {"USDT": 1000.0}}
    
    async def fetch_withdrawal_fee(self, code: str) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        fees = {
            "BTC": 0.0005,
            "ETH": 0.01,
            "USDT": 1.0,
        }
        return {
            "currency": code,
            "withdraw": {
                "fee": fees.get(code.upper(), 0.1),
                "networks": {}
            }
        }
    
    async def fetch_trading_fee(self, symbol: str) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        return {
            "symbol": symbol,
            "taker": 0.001,
            "maker": 0.001
        }
    
    async def fetch_deposit_address(self, code: str) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        addresses = {
            "BTC": "mock_btc_address_12345",
            "ETH": "mock_eth_address_12345",
            "USDT": "mock_usdt_address_12345",
        }
        return {
            "currency": code,
            "address": addresses.get(code.upper(), "mock_default_address"),
            "tag": None
        }
    
    async def create_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: Decimal,
        price: Decimal | None = None,
    ) -> dict[str, Any]:
        self.create_order_count += 1
        if self.exception_to_raise:
            raise self.exception_to_raise
        await asyncio.sleep(0.01)
        
        return {
            "id": f"mock_order_{self.create_order_count}",
            "symbol": symbol,
            "type": type,
            "side": side,
            "status": "closed",
            "filled": float(amount),
            "average": float(price) if price else 100.0,
            "fee": {"cost": 0.5, "currency": "USDT"},
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
        }
    
    async def withdraw(
        self,
        code: str,
        amount: Decimal,
        address: str,
        params: dict[str, Any] = {},
    ) -> dict[str, Any]:
        self.withdraw_count += 1
        if self.exception_to_raise:
            raise self.exception_to_raise
        await asyncio.sleep(0.01)
        
        return {
            "id": f"mock_withdraw_{self.withdraw_count}",
            "currency": code,
            "amount": float(amount),
            "address": address,
            "status": "pending",
            "fee": {"cost": 0.0005, "currency": code},
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
        }