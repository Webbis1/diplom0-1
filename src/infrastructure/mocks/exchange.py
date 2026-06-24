import logging
from decimal import Decimal

from src.core.dto.ticker import Ticker

from ..base import Exchange as BaseExchange
from src.application.interfaces import Api
from src.core.dto.market_info import MarketInfo
from src.core.entities import Coin


class MockExchange(BaseExchange):
    
    @property
    def __logger(self):
        return logging.getLogger(f'MockExchange for {self.name}')
    
    async def _balance_request(self, api: "Api"):
        balance = await api.watch_balance()
        self.__logger.info(balance)
        
    async def _price_request(self, api: "Api"):
        ticker : Ticker = await api.watch_ticker("BTC/USDT")
        self.__logger.info(ticker)
        self._notify_price_sub(ticker.)
    
    async def get_markets(self) -> list[MarketInfo]:
        usdt = Coin(address="usdt", symbol="USDT")
        btc = Coin(address="btc", symbol="BTC")
        eth = Coin(address="eth", symbol="ETH")
        
        return [
            MarketInfo(base=btc, quote=usdt, taker_fee=Decimal("0.001"), min_amount=Decimal(0.5), active=True),
            MarketInfo(base=eth, quote=usdt, taker_fee=Decimal("0.001"), min_amount=Decimal(0.5), active=True),
        ]
    
    async def get_available_coins(self) -> list[Coin]:
        return [
            Coin(address="usdt", symbol="USDT"),
            Coin(address="btc", symbol="BTC"),
            Coin(address="eth", symbol="ETH"),
        ]
    
    async def get_withdrawal_fee(self, coin: Coin) -> Decimal:
        fees = {
            "btc": Decimal("0.0005"),
            "eth": Decimal("0.01"),
            "usdt": Decimal("1.0"),
        }
        return fees.get(coin.symbol.lower(), Decimal("0.1"))
    
    async def get_initial_price(self, coin: Coin) -> Decimal:
        prices = {
            "btc": Decimal("50000.0"),
            "eth": Decimal("3000.0"),
            "usdt": Decimal("1.0"),
        }
        return prices.get(coin.symbol.lower(), Decimal("1.0"))
    
    async def get_trading_fee(self, base: Coin, quote: Coin) -> Decimal:
        return Decimal("0.001")
    
    async def get_deposit_address(self, coin: Coin) -> str:
        addresses = {
            "btc": "mock_btc_address_12345",
            "eth": "mock_eth_address_12345",
            "usdt": "mock_usdt_address_12345",
        }
        return addresses.get(coin.symbol.lower(), "mock_default_address")