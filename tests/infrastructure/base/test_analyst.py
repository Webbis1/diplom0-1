from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
from typing import AsyncGenerator
import pytest

from src.infrastructure.base.analyst import Analyst
from src.application.logic.graph import Graph
from src.core.entities.potential import Potential


class TestAnalystSingleton:
    def test_singleton_pattern(self) -> None:
        analyst1 = Analyst([])
        analyst2 = Analyst([])
        
        assert analyst1 is analyst2

    def test_singleton_with_different_args(self) -> None:
        ex1 = MagicMock()
        ex2 = MagicMock()
        
        analyst1 = Analyst([ex1])
        analyst2 = Analyst([ex2])
        
        assert analyst1 is analyst2


class TestAnalystTopology:
    @pytest.mark.asyncio
    async def test_build_topology_creates_transfer_edges(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin = MagicMock()
        
        exchange_a = MagicMock()
        exchange_a.get_available_coins = AsyncMock(return_value=[coin])
        exchange_a.get_initial_price = AsyncMock(return_value=Decimal("100.0"))
        exchange_a.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.0"))
        
        exchange_b = MagicMock()
        exchange_b.get_available_coins = AsyncMock(return_value=[coin])
        exchange_b.get_initial_price = AsyncMock(return_value=Decimal("105.0"))
        exchange_b.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.5"))
        
        exchange_a.get_usdt = MagicMock(return_value=MagicMock())
        exchange_a.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))

        exchange_b.get_usdt = MagicMock(return_value=MagicMock())
        exchange_b.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))
        
        analyst._exchanges = [exchange_a, exchange_b]
        
        await analyst._build_topology()
        
        assert coin in analyst._graph.nodes
        assert exchange_a in analyst._graph.nodes[coin]
        assert exchange_b in analyst._graph.nodes[coin]
        
        node_a = analyst._graph.nodes[coin][exchange_a]
        node_b = analyst._graph.nodes[coin][exchange_b]
        
        assert len(node_a.get_outgoing_edges()) == 1
        assert len(node_b.get_outgoing_edges()) == 1
        
        edge_a_to_b = node_a.get_outgoing_edges()[0]
        assert edge_a_to_b.get_destination() == node_b
        
        edge_b_to_a = node_b.get_outgoing_edges()[0]
        assert edge_b_to_a.get_destination() == node_a

    @pytest.mark.asyncio
    async def test_build_topology_skips_single_exchange_coins(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin_single = MagicMock()
        coin_shared = MagicMock()
        
        exchange_a = MagicMock()
        exchange_a.get_available_coins = AsyncMock(return_value=[coin_single, coin_shared])
        exchange_a.get_initial_price = AsyncMock(return_value=Decimal("100.0"))
        exchange_a.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.0"))
        
        exchange_b = MagicMock()
        exchange_b.get_available_coins = AsyncMock(return_value=[coin_shared])
        exchange_b.get_initial_price = AsyncMock(return_value=Decimal("105.0"))
        exchange_b.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.5"))
        
        exchange_a.get_usdt = MagicMock(return_value=MagicMock())
        exchange_a.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))

        exchange_b.get_usdt = MagicMock(return_value=MagicMock())
        exchange_b.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))
        
        analyst._exchanges = [exchange_a, exchange_b]
        
        await analyst._build_topology()
        
        assert coin_single not in analyst._graph.nodes
        assert coin_shared in analyst._graph.nodes

    @pytest.mark.asyncio
    async def test_build_topology_multiple_coins(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin1 = MagicMock()
        coin2 = MagicMock()
        coin3 = MagicMock()
        
        exchange_a = MagicMock()
        exchange_a.get_available_coins = AsyncMock(return_value=[coin1, coin2, coin3])
        exchange_a.get_initial_price = AsyncMock(return_value=Decimal("100.0"))
        exchange_a.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.0"))
        
        exchange_b = MagicMock()
        exchange_b.get_available_coins = AsyncMock(return_value=[coin1, coin2])
        exchange_b.get_initial_price = AsyncMock(return_value=Decimal("105.0"))
        exchange_b.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.5"))
        
        exchange_a.get_usdt = MagicMock(return_value=MagicMock())
        exchange_a.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))

        exchange_b.get_usdt = MagicMock(return_value=MagicMock())
        exchange_b.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))
        
        
        analyst._exchanges = [exchange_a, exchange_b]
        
        await analyst._build_topology()
        
        assert coin1 in analyst._graph.nodes
        assert coin2 in analyst._graph.nodes
        assert coin3 not in analyst._graph.nodes

    @pytest.mark.asyncio
    async def test_build_topology_withdrawal_fees_called_once(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin = MagicMock()
        
        exchange_a = MagicMock()
        exchange_a.get_available_coins = AsyncMock(return_value=[coin])
        exchange_a.get_initial_price = AsyncMock(return_value=Decimal("100.0"))
        exchange_a.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.0"))
        
        exchange_b = MagicMock()
        exchange_b.get_available_coins = AsyncMock(return_value=[coin])
        exchange_b.get_initial_price = AsyncMock(return_value=Decimal("105.0"))
        exchange_b.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.5"))
        
        
        exchange_a.get_usdt = MagicMock(return_value=MagicMock())
        exchange_a.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))

        exchange_b.get_usdt = MagicMock(return_value=MagicMock())
        exchange_b.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))
        
        analyst._exchanges = [exchange_a, exchange_b]
        
        await analyst._build_topology()
        
        assert exchange_a.get_withdrawal_fee.call_count == 1
        assert exchange_b.get_withdrawal_fee.call_count == 1
        
    @pytest.mark.asyncio
    async def test_build_topology_creates_trading_edges(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        usdt = MagicMock()
        btc = MagicMock()
        
        exchange_a = MagicMock()
        exchange_a.get_usdt = MagicMock(return_value=usdt)
        exchange_a.get_available_coins = AsyncMock(return_value=[usdt, btc])
        exchange_a.get_initial_price = AsyncMock(return_value=Decimal("100.0"))
        exchange_a.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.0"))
        exchange_a.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))
        
        exchange_b = MagicMock()
        exchange_b.get_usdt = MagicMock(return_value=usdt)
        exchange_b.get_available_coins = AsyncMock(return_value=[usdt, btc])
        exchange_b.get_initial_price = AsyncMock(return_value=Decimal("105.0"))
        exchange_b.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.5"))
        exchange_b.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))
        
        analyst._exchanges = [exchange_a, exchange_b]
        
        await analyst._build_topology()
        
        usdt_node_a = analyst._graph.nodes[usdt][exchange_a]
        btc_node_a = analyst._graph.nodes[btc][exchange_a]
        
        outgoing_from_btc = btc_node_a.get_outgoing_edges()
        trading_edges_a = [e for e in outgoing_from_btc if e.get_destination() == usdt_node_a]
        assert len(trading_edges_a) == 1
        
        outgoing_from_usdt = usdt_node_a.get_outgoing_edges()
        trading_edges_back = [e for e in outgoing_from_usdt if e.get_destination() == btc_node_a]
        assert len(trading_edges_back) == 1
        
        exchange_a.get_trading_fee.assert_called_with(btc, usdt)

    @pytest.mark.asyncio
    async def test_build_topology_skips_trading_when_coin_missing(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        usdt = MagicMock()
        btc = MagicMock()
        
        exchange_a = MagicMock()
        exchange_a.get_usdt = MagicMock(return_value=usdt)
        exchange_a.get_available_coins = AsyncMock(return_value=[btc])
        exchange_a.get_initial_price = AsyncMock(return_value=Decimal("50000.0"))
        exchange_a.get_withdrawal_fee = AsyncMock(return_value=Decimal("0.0005"))
        exchange_a.get_trading_fee = AsyncMock(return_value=Decimal("0.001"))
        
        analyst._exchanges = [exchange_a]
        
        await analyst._build_topology()
        
        assert usdt not in analyst._graph.nodes
        exchange_a.get_trading_fee.assert_not_called()

    @pytest.mark.asyncio
    async def test_build_topology_trading_fee_applied_correctly(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        usdt = MagicMock()
        eth = MagicMock()
        
        exchange_a = MagicMock()
        exchange_a.get_usdt = MagicMock(return_value=usdt)
        exchange_a.get_available_coins = AsyncMock(return_value=[usdt, eth])
        exchange_a.get_initial_price = AsyncMock(return_value=Decimal("3000.0"))
        exchange_a.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.0"))
        exchange_a.get_trading_fee = AsyncMock(return_value=Decimal("0.002"))
        
        exchange_b = MagicMock()
        exchange_b.get_usdt = MagicMock(return_value=usdt)
        exchange_b.get_available_coins = AsyncMock(return_value=[usdt, eth])
        exchange_b.get_initial_price = AsyncMock(return_value=Decimal("3010.0"))
        exchange_b.get_withdrawal_fee = AsyncMock(return_value=Decimal("1.5"))
        exchange_b.get_trading_fee = AsyncMock(return_value=Decimal("0.002"))
        
        analyst._exchanges = [exchange_a, exchange_b]
        
        await analyst._build_topology()
        
        eth_node_a = analyst._graph.nodes[eth][exchange_a]
        trading_edge = [e for e in eth_node_a.get_outgoing_edges() 
                       if e.get_destination() == analyst._graph.nodes[usdt][exchange_a]][0]
        
        assert trading_edge.get_fixed_fee() == Decimal("0.0")
    
        
        
class TestAnalystSubscription:
    @pytest.mark.asyncio
    async def test_subscribe_filters_coins_before_subscribing(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin_on_ex = MagicMock()
        coin_off_ex = MagicMock()
        exchange = MagicMock()
        other_exchange = MagicMock()
        
        analyst._graph.nodes = {
            coin_on_ex: {exchange: MagicMock()},
            coin_off_ex: {other_exchange: MagicMock()}
        }
        
        captured_coins: set | None = None
        
        async def mock_subscribe(coins: set) -> AsyncGenerator[MagicMock, None]:
            nonlocal captured_coins
            captured_coins = coins
            yield MagicMock(coin=coin_on_ex, price=Decimal("100.0"))
            
        exchange.subscribe_price = mock_subscribe
        
        await analyst._subscribe_to_exchange(exchange)
        
        assert captured_coins is not None
        assert coin_on_ex in captured_coins
        assert coin_off_ex not in captured_coins

    @pytest.mark.asyncio
    async def test_subscribe_updates_graph_prices(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin = MagicMock()
        exchange = MagicMock()
        
        analyst._graph.nodes = {coin: {exchange: MagicMock()}}
        
        ticker1 = MagicMock(coin=coin, price=Decimal("100.0"))
        ticker2 = MagicMock(coin=coin, price=Decimal("101.0"))
        ticker3 = MagicMock(coin=coin, price=Decimal("99.0"))
        
        async def mock_subscribe(coins: set) -> AsyncGenerator[MagicMock, None]:
            yield ticker1
            yield ticker2
            yield ticker3
            
        exchange.subscribe_price = mock_subscribe
        
        with patch.object(analyst._graph, 'ensure_node', new_callable=AsyncMock) as mock_ensure:
            await analyst._subscribe_to_exchange(exchange)
            
            assert mock_ensure.call_count == 3
            mock_ensure.assert_any_call(coin, exchange, Decimal("100.0"))
            mock_ensure.assert_any_call(coin, exchange, Decimal("101.0"))
            mock_ensure.assert_any_call(coin, exchange, Decimal("99.0"))

    @pytest.mark.asyncio
    async def test_subscribe_propagates_stream_errors(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        exchange = MagicMock()
        
        async def mock_subscribe(coins: set) -> AsyncGenerator[MagicMock, None]:
            yield MagicMock(coin=MagicMock(), price=Decimal("100.0"))
            raise ConnectionError("Network down")
            
        exchange.subscribe_price = mock_subscribe
        
        with pytest.raises(ConnectionError):
            await analyst._subscribe_to_exchange(exchange)


class TestAnalystLifecycle:
    @pytest.mark.asyncio
    async def test_launch_starts_graph_and_subscriptions(self) -> None:
        ex1 = MagicMock()
        ex2 = MagicMock()
        analyst = Analyst([ex1, ex2])
        analyst._initialized = False
        analyst.__init__([ex1, ex2])
        
        tg = MagicMock()
        
        with patch.object(analyst, '_build_topology', new_callable=AsyncMock) as mock_build:
            await analyst.launch(tg)
            
            mock_build.assert_awaited_once()
            assert tg.create_task.call_count == 3
            
            
    @pytest.mark.asyncio
    async def test_stop_stops_graph(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        with patch.object(analyst._graph, 'stop', new_callable=AsyncMock) as mock_stop:
            await analyst.stop()
            mock_stop.assert_awaited_once()


class TestAnalystRouting:
    @pytest.mark.asyncio
    async def test_returns_none_when_coin_missing(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        result = await analyst.get_optimal_route(MagicMock(), MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_exchange_missing(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin = MagicMock()
        analyst._graph.nodes = {coin: {}}
        
        result = await analyst.get_optimal_route(coin, MagicMock())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_outgoing_edges(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin = MagicMock()
        exchange = MagicMock()
        mock_node = MagicMock()
        mock_node.get_outgoing_edges.return_value = []
        
        analyst._graph.nodes = {coin: {exchange: mock_node}}
        
        result = await analyst.get_optimal_route(coin, exchange)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_best_potential_below_barrier(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin = MagicMock()
        exchange = MagicMock()
        
        weak_potential = Potential(a=Decimal("0.9"), b=Decimal("0.0"))
        mock_edge = MagicMock()
        mock_edge.get_potential.return_value = weak_potential
        
        mock_node = MagicMock()
        mock_node.get_outgoing_edges.return_value = [mock_edge]
        
        analyst._graph.nodes = {coin: {exchange: mock_node}}
        
        result = await analyst.get_optimal_route(coin, exchange)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_route_candidate_when_profitable(self) -> None:
        analyst = Analyst([])
        analyst._initialized = False
        analyst.__init__([])
        
        coin = MagicMock()
        exchange = MagicMock()
        
        dest_node = MagicMock()
        profitable_potential = Potential(a=Decimal("1.05"), b=Decimal("10.0"))
        
        mock_edge = MagicMock()
        mock_edge.get_potential.return_value = profitable_potential
        mock_edge.get_destination.return_value = dest_node
        
        mock_node = MagicMock()
        mock_node.get_outgoing_edges.return_value = [mock_edge]
        
        analyst._graph.nodes = {coin: {exchange: mock_node}}
        
        result = await analyst.get_optimal_route(coin, exchange)
        
        assert result is not None
        assert result.multiplier == Decimal("1.05")
        assert result.residual_value == Decimal("10.0")
        assert result.departure == mock_node
        assert result.destination == dest_node
        assert result.edge == mock_edge