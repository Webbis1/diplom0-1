import asyncio
from decimal import Decimal
from datetime import datetime
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.base.exchange import Exchange
from src.core.entities import Exchange as ExchangeModel, Coin
from src.core.dto import Asset, Ticker, MarketInfo, Order
from src.application.interfaces import Connection as IConnection, Api


class ConcreteExchange(Exchange):
    """Тестовая реализация абстрактного класса Exchange"""
    
    async def _balance_request(self, api: "Api") -> None:
        # Заглушка для абстрактного метода
        pass
    
    async def _price_request(self, api: "Api") -> None:
        # Заглушка для абстрактного метода
        pass
    
    async def get_markets(self) -> list[MarketInfo]:
        # Заглушка для абстрактного метода
        return []


@pytest.fixture
def mock_connection():
    """Фикстура для мокированного соединения"""
    conn = MagicMock(spec=IConnection)
    conn.working = True
    return conn


@pytest.fixture
def mock_api():
    """Фикстура для мокированного API"""
    api = AsyncMock(spec=Api)
    return api


@pytest.fixture
def exchange(mock_connection):
    """Фикстура для создания экземпляра Exchange"""
    info = ExchangeModel(name="test_exchange", address_list={})
    return ConcreteExchange(info=info, conn=mock_connection)


class TestExchangeSubscriptions:
    """Тесты для методов подписки"""
    
    @pytest.mark.asyncio
    async def test_subscribe_price_yields_ticker(self, exchange: Exchange) -> None:
        """Проверяем, что subscribe_price возвращает тикеры"""
        coin = Coin(address="0x0000000000000000000000000000000000000000", symbol="BTC")
        coins = {coin}
        
        exchange._working.set()
        
        # Запускаем генератор как отдельную задачу
        generator = exchange.subscribe_price(coins)
        async def get_next() -> Ticker:
            return await generator.__anext__()

        task = asyncio.create_task(get_next())
                
        # Даем задаче запуститься
        await asyncio.sleep(0.01)
        
        # Уведомляем о новой цене
        exchange._notify_price_sub(coin, Decimal("50000.0"))
        
        # Получаем результат с таймаутом
        try:
            ticker = await asyncio.wait_for(task, timeout=1.0)
            assert isinstance(ticker, Ticker)
            assert ticker.coin == coin
            assert ticker.price == Decimal("50000.0")
        finally:
            exchange._working.clear()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_subscribe_balance_yields_asset(self, exchange: Exchange) -> None:
        """Проверяем, что subscribe_balance возвращает активы"""
        coin = Coin(address="0x0000000000000000000000000000000000000000", symbol="BTC")
        coins = {coin}
        
        exchange._working.set()
        
        generator = exchange.subscribe_balance(coins)
        async def get_next() -> Asset:
            return await generator.__anext__()

        task = asyncio.create_task(get_next())
        
        await asyncio.sleep(0.01)
        
        exchange._notify_balance_sub(coin, Decimal("1.5"))
        
        try:
            asset = await asyncio.wait_for(task, timeout=1.0)
            assert isinstance(asset, Asset)
            assert asset.coin == coin
            assert asset.amount == Decimal("1.5")
        finally:
            exchange._working.clear()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_subscribe_filters_by_coin_set(self, exchange: Exchange) -> None:
        """Проверяем, что подписка фильтрует по набору монет"""
        btc = Coin(address="0x0000000000000000000000000000000000000001", symbol="BTC")
        eth = Coin(address="0x0000000000000000000000000000000000000002", symbol="ETH")
        coins = {btc}  # Подписываемся только на BTC
        
        exchange._working.set()
        
        generator = exchange.subscribe_price(coins)
        async def get_next() -> Ticker:
            return await generator.__anext__()

        task = asyncio.create_task(get_next())
        
        await asyncio.sleep(0.01)
        
        # Уведомляем о ценах обеих монет
        exchange._notify_price_sub(eth, Decimal("3000.0"))
        exchange._notify_price_sub(btc, Decimal("50000.0"))
        
        try:
            ticker = await asyncio.wait_for(task, timeout=1.0)
            # Должен получить только BTC
            assert ticker.coin == btc
            assert ticker.price == Decimal("50000.0")
        finally:
            exchange._working.clear()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


class TestExchangeLifecycle:
    """Тесты для методов жизненного цикла"""
    
    @pytest.mark.asyncio
    async def test_launch_sets_working_flag(self, exchange: Exchange) -> None:
        tg = MagicMock()
        
        # Мокаем run_*_observer, чтобы они не блокировали тест
        with patch.object(exchange, 'run_balance_observer', new_callable=AsyncMock), \
            patch.object(exchange, 'run_price_observer', new_callable=AsyncMock):
            
            await exchange.launch(tg)
            
            assert exchange.working is True
            assert tg.create_task.call_count == 2
    
    @pytest.mark.asyncio
    async def test_stop_clears_working_flag(self, exchange: Exchange) -> None:
        """Проверяем, что stop сбрасывает флаг working"""
        exchange._working.set()
        
        await exchange.stop()
        
        assert exchange.working is False


class TestExchangeApiMethods:
    """Тесты для методов, работающих через API"""
    
    @pytest.mark.asyncio
    async def test_get_withdrawal_fee_returns_fee(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем получение комиссии за вывод"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        
        # Настраиваем mock
        mock_api.fetch_withdrawal_fee.return_value = {
            "withdraw": {"fee": 0.0005}
        }
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        fee = await exchange.get_withdrawal_fee(coin)
        
        assert fee == Decimal("0.0005")
        mock_api.fetch_withdrawal_fee.assert_called_once_with("BTC")
    
    @pytest.mark.asyncio
    async def test_get_withdrawal_fee_returns_default_on_error(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем, что при ошибке возвращается значение по умолчанию"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        
        # Настраиваем mock для выброса исключения
        mock_api.fetch_withdrawal_fee.side_effect = Exception("API error")
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        fee = await exchange.get_withdrawal_fee(coin)
        
        assert fee == Decimal("1.0")
    
    @pytest.mark.asyncio
    async def test_get_initial_price_returns_price(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем получение начальной цены"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        
        # Настраиваем mock
        mock_api.fetch_ticker.return_value = {
            "last": 50000.0
        }
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        price = await exchange.get_initial_price(coin)
        
        assert price == Decimal("50000.0")
        mock_api.fetch_ticker.assert_called_once_with("BTC/USDT")
    
    @pytest.mark.asyncio
    async def test_get_trading_fee_returns_fee(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем получение торговой комиссии"""
        base = Coin(symbol="BTC", address="Bitcoin")
        quote = Coin(symbol="USDT", address="Tether")
        
        # Настраиваем mock
        mock_api.fetch_trading_fee.return_value = {
            "taker": 0.001
        }
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        fee = await exchange.get_trading_fee(base, quote)
        
        assert fee == Decimal("0.001")
        mock_api.fetch_trading_fee.assert_called_once_with("BTC/USDT")
    
    @pytest.mark.asyncio
    async def test_get_deposit_address_returns_address(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем получение адреса депозита"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        
        # Настраиваем mock
        mock_api.fetch_deposit_address.return_value = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        }
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        address = await exchange.get_deposit_address(coin)
        
        assert address == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        mock_api.fetch_deposit_address.assert_called_once_with("BTC")


class TestExchangeTradingOperations:
    """Тесты для торговых операций"""
    
    @pytest.mark.asyncio
    async def test_buy_creates_order(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем создание ордера на покупку"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        asset = Asset(coin=coin, amount=Decimal("0.1"))
        
        # Настраиваем mock
        mock_api.create_order.return_value = {
            "id": "order_123",
            "filled": 0.1,
            "average": 50000.0,
            "fee": {"cost": 50.0},
            "timestamp": 1234567890000,
            "status": "closed"
        }
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        order = await exchange.buy(asset)
        
        assert isinstance(order, Order)
        assert order.id == "order_123"
        assert order.type == "buy"
        assert order.coin == coin
        assert order.amount == Decimal("0.1")
        assert order.price == Decimal("50000.0")
        assert order.fee == Decimal("50.0")
        assert order.status == "filled"
        
        mock_api.create_order.assert_called_once_with(
            symbol="BTC/USDT",
            type="market",
            side="buy",
            amount=Decimal("0.1"),
            price=None
        )
    
    @pytest.mark.asyncio
    async def test_sell_creates_order(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем создание ордера на продажу"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        asset = Asset(coin=coin, amount=Decimal("0.1"))
        
        # Настраиваем mock
        mock_api.create_order.return_value = {
            "id": "order_456",
            "filled": 0.1,
            "average": 50000.0,
            "fee": {"cost": 50.0},
            "timestamp": 1234567890000,
            "status": "closed"
        }
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        order = await exchange.sell(asset)
        
        assert isinstance(order, Order)
        assert order.id == "order_456"
        assert order.type == "sell"
        assert order.coin == coin
        assert order.amount == Decimal("0.1")
        assert order.price == Decimal("50000.0")
        assert order.fee == Decimal("50.0")
        assert order.status == "filled"
        
        mock_api.create_order.assert_called_once_with(
            symbol="BTC/USDT",
            type="market",
            side="sell",
            amount=Decimal("0.1"),
            price=None
        )
    
    @pytest.mark.asyncio
    async def test_transfer_creates_withdrawal(self, exchange: Exchange, mock_connection, mock_api) -> None:
        """Проверяем создание перевода"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        asset = Asset(coin=coin, amount=Decimal("0.1"))
        
        # Создаем мок для биржи-получателя
        destination = AsyncMock()
        destination.get_deposit_address.return_value = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        
        # Настраиваем mock
        mock_api.withdraw.return_value = {
            "id": "tx_789",
            "fee": {"cost": 0.0005},
            "timestamp": 1234567890000,
            "status": "pending"
        }
        mock_connection.client.return_value.__aenter__.return_value = mock_api
        
        order = await exchange.transfer(asset, destination)
        
        assert isinstance(order, Order)
        assert order.id == "tx_789"
        assert order.type == "transfer"
        assert order.coin == coin
        assert order.amount == Decimal("0.1")
        assert order.price is None
        assert order.fee == Decimal("0.0005")
        assert order.status == "pending"
        
        destination.get_deposit_address.assert_called_once_with(coin)
        mock_api.withdraw.assert_called_once_with(
            symbol="BTC",
            amount=Decimal("0.1"),
            address="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        )
    
    @pytest.mark.asyncio
    async def test_buy_raises_error_when_api_unavailable(self, exchange: Exchange, mock_connection) -> None:
        """Проверяем, что buy выбрасывает ошибку, если API недоступен"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        asset = Asset(coin=coin, amount=Decimal("0.1"))
        
        # Настраиваем mock для возврата None
        mock_connection.client.return_value.__aenter__.return_value = None
        
        with pytest.raises(RuntimeError, match="API client is not available"):
            await exchange.buy(asset)


class TestExchangeQueueOverflow:
    """Тесты для обработки переполнения очередей"""
    
    @pytest.mark.asyncio
    async def test_notify_price_sub_handles_queue_full(self, exchange: Exchange) -> None:
        """Проверяем, что уведомление обрабатывает переполнение очереди"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        
        # Создаем очередь с maxsize=1
        q = asyncio.Queue(maxsize=1)
        exchange._price_sub.append(q)
        
        # Заполняем очередь
        await q.put(Ticker(coin, Decimal("49000.0")))
        
        # Уведомляем о новой цене (должна вытеснить старую)
        exchange._notify_price_sub(coin, Decimal("50000.0"))
        
        # Получаем тикер из очереди
        ticker = await q.get()
        
        assert ticker.price == Decimal("50000.0")
    
    @pytest.mark.asyncio
    async def test_notify_balance_sub_handles_queue_full(self, exchange: Exchange) -> None:
        """Проверяем, что уведомление баланса обрабатывает переполнение очереди"""
        coin = Coin(symbol="BTC", address="Bitcoin")
        
        # Создаем очередь с maxsize=1
        q = asyncio.Queue(maxsize=1)
        exchange._balance_sub.append(q)
        
        # Заполняем очередь
        await q.put(Asset(coin, Decimal("1.0")))
        
        # Уведомляем о новом балансе (должен вытеснить старый)
        exchange._notify_balance_sub(coin, Decimal("2.0"))
        
        # Получаем актив из очереди
        asset = await q.get()
        
        assert asset.amount == Decimal("2.0")