import asyncio
from decimal import Decimal
import logging
import random
import string
from typing import Any

class MockApi:
    def __init__(self, coins: list[str] | None = None):
        self.has: dict[str, bool] = {
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

        if coins is None:
            random_coins = {"".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5))) for _ in range(99)}
            self._coins = ["USDT"] + list(random_coins)
        else:
            self._coins = coins
        self._prices: dict[str, float] = {}
        self._withdrawal_fees: dict[str, float] = {}
        self._trading_fees: dict[str, float] = {}
        self._deposit_addresses: dict[str, str] = {}
        self._min_amounts: dict[str, float] = {}

        self._initialize_mock_data()

    def _initialize_mock_data(self) -> None:
        for coin in self._coins:
            if coin == "USDT":
                self._prices[f"{coin}/USDT"] = 1.0
            elif coin == "BTC":
                self._prices[f"{coin}/USDT"] = random.uniform(45000.0, 55000.0)
            elif coin == "ETH":
                self._prices[f"{coin}/USDT"] = random.uniform(2500.0, 3500.0)
            else:
                self._prices[f"{coin}/USDT"] = random.uniform(10.0, 1000.0)

            self._withdrawal_fees[coin] = random.uniform(0.0001, 0.01) if coin != "USDT" else random.uniform(0.5, 2.0)
            self._trading_fees[coin] = random.uniform(0.0005, 0.002)
            self._deposit_addresses[coin] = f"mock_{coin.lower()}_address_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            self._min_amounts[coin] = random.uniform(0.1, 1.0)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger("MockApi")

    async def fetch_markets(self) -> list[dict[str, Any]]:
        markets = []
        usdt = "USDT"
        for coin in self._coins:
            if coin == usdt:
                continue
            markets.append({
                "symbol": f"{coin}/{usdt}",
                "base": coin,
                "quote": usdt,
                "active": True,
                "taker": self._trading_fees[coin],
                "maker": self._trading_fees[coin],
                "limits": {
                    "amount": {
                        "min": self._min_amounts[coin]
                    }
                }
            })
        return markets

    async def load_markets(self) -> None:
        self.load_markets_count += 1
        if self.exception_to_raise:
            raise self.exception_to_raise
        await asyncio.sleep(0.01)

    async def close(self) -> None:
        self.close_count += 1
        await asyncio.sleep(0.01)

    async def watch_ticker(self, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            await asyncio.sleep(0.3)
            if params is None:
                params = {}

            if symbol not in self._prices:
                base = symbol.split("/")[0]
                if base == "BTC":
                    self._prices[symbol] = random.uniform(45000.0, 55000.0)
                elif base == "ETH":
                    self._prices[symbol] = random.uniform(2500.0, 3500.0)
                else:
                    self._prices[symbol] = random.uniform(10.0, 1000.0)

            self._prices[symbol] *= random.uniform(0.995, 1.005)
            price = self._prices[symbol]

            return {
                "symbol": symbol,
                "high": price * 1.01,
                "low": price * 0.99,
                "close": price,
                "last": price
            }
        except asyncio.CancelledError:
            self.logger.info("Cancel in watch_ticker")
            raise

    async def watch_balance(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            await asyncio.sleep(2)
            free = {}
            for coin in self._coins:
                if coin == "USDT":
                    free[coin] = random.uniform(500.0, 2000.0)
                else:
                    free[coin] = random.uniform(0.01, 10.0)
            return {"total": free.copy(), "free": free}
        except asyncio.CancelledError:
            self.logger.info("Cancel in watch_balance")
            raise

    async def fetch_ticker(self, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        if params is None:
            params = {}
        price = self._prices.get(symbol, 100.0)
        return {"symbol": symbol, "last": price}

    async def fetch_balance(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        if params is None:
            params = {}
        free = {}
        for coin in self._coins:
            free[coin] = random.uniform(0.01, 10.0)
        return {"free": free}

    async def fetch_withdrawal_fee(self, code: str) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        fee = self._withdrawal_fees.get(code.upper(), 0.1)
        return {
            "currency": code,
            "withdraw": {
                "fee": fee,
                "networks": {}
            }
        }

    async def fetch_trading_fee(self, symbol: str) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        base = symbol.split("/")[0]
        fee = self._trading_fees.get(base.upper(), 0.001)
        return {
            "symbol": symbol,
            "taker": fee,
            "maker": fee
        }

    async def fetch_deposit_address(self, code: str) -> dict[str, Any]:
        if self.exception_to_raise:
            raise self.exception_to_raise
        address = self._deposit_addresses.get(code.upper(), f"mock_{code.lower()}_address")
        return {
            "currency": code,
            "address": address,
            "tag": None
        }

    async def create_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: "Decimal",
        price: "Decimal | None" = None,
    ) -> dict[str, Any]:
        self.create_order_count += 1
        if self.exception_to_raise:
            raise self.exception_to_raise
        await asyncio.sleep(0.01)
        
        avg_price = float(price) if price else self._prices.get(symbol, 100.0)
        
        return {
            "id": f"mock_order_{self.create_order_count}",
            "symbol": symbol,
            "type": type,
            "side": side,
            "status": "closed",
            "filled": float(amount),
            "average": avg_price,
            "fee": {"cost": 0.5, "currency": "USDT"},
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
        }

    async def withdraw(
        self,
        code: str,
        amount: "Decimal",
        address: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.withdraw_count += 1
        if self.exception_to_raise:
            raise self.exception_to_raise
        if params is None:
            params = {}
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