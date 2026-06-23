from __future__ import annotations

import asyncio
import random
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.core.logic.graph import Graph


class TestGraphWaveRelaxation:
    @pytest.mark.asyncio
    async def test_wave_convergence_with_three_nodes(self) -> None:
        graph = Graph()
        await graph.start()
        
        try:
            coin_usdt = MagicMock()
            coin_btc = MagicMock()
            exchange_a = MagicMock()
            exchange_b = MagicMock()
            
            node1 = await graph.ensure_node(coin_usdt, exchange_a, Decimal("1.0"))
            node2 = await graph.ensure_node(coin_btc, exchange_a, Decimal("50000.0"))
            node3 = await graph.ensure_node(coin_usdt, exchange_b, Decimal("1.0"))
            
            await graph.ensure_edge(node1, node2, Decimal("0.001"), Decimal("0.0"))
            await graph.ensure_edge(node2, node3, Decimal("0.0"), Decimal("0.0001"))
            
            await asyncio.wait_for(graph.wait_completion(), timeout=2.0)
            
            assert node1.get_potential() is not None
            assert node2.get_potential() is not None
            assert node3.get_potential() is not None
            
        finally:
            await graph.stop()

    @pytest.mark.asyncio
    async def test_multiple_price_updates_coalesce(self) -> None:
        graph = Graph()
        await graph.start()
        
        try:
            coin = MagicMock()
            exchange = MagicMock()
            
            await graph.ensure_node(coin, exchange, Decimal("100.0"))
            
            for price in [Decimal("101.0"), Decimal("102.0"), Decimal("103.0")]:
                await graph.ensure_node(coin, exchange, price)
            
            await asyncio.wait_for(graph.wait_completion(), timeout=2.0)
            
            node = graph.nodes[coin][exchange]
            assert node.get_price() == Decimal("103.0")
            
        finally:
            await graph.stop()

    @pytest.mark.asyncio
    async def test_graph_stop_terminates_worker(self) -> None:
        graph = Graph()
        await graph.start()
        
        coin = MagicMock()
        exchange = MagicMock()
        await graph.ensure_node(coin, exchange, Decimal("100.0"))
        
        await asyncio.wait_for(graph.wait_completion(), timeout=2.0)
        await graph.stop()
        
        assert not graph._working.is_set()


class TestGraphScaleAndTopology:
    @pytest.mark.asyncio
    async def test_large_scale_chain_convergence(self) -> None:
        graph = Graph()
        await graph.start()
        
        try:
            coins = [MagicMock() for _ in range(50)]
            exchange = MagicMock()
            
            nodes = []
            for i in range(50):
                node = await graph.ensure_node(coins[i], exchange, Decimal("100.0"))
                nodes.append(node)
                
            for i in range(49):
                await graph.ensure_edge(nodes[i], nodes[i+1], Decimal("0.001"), Decimal("0.0"))
                
            await graph.ensure_node(coins[49], exchange, Decimal("200.0"))
            await asyncio.wait_for(graph.wait_completion(), timeout=3.0)
            
        finally:
            await graph.stop()

    @pytest.mark.asyncio
    async def test_cyclic_graph_convergence(self) -> None:
        graph = Graph()
        await graph.start()
        
        try:
            coins = [MagicMock() for _ in range(5)]
            exchange = MagicMock()
            
            nodes = []
            for i in range(5):
                node = await graph.ensure_node(coins[i], exchange, Decimal("100.0"))
                nodes.append(node)
                
            for i in range(5):
                await graph.ensure_edge(nodes[i], nodes[(i + 1) % 5], Decimal("0.001"), Decimal("0.0"))
                
            await graph.ensure_node(coins[4], exchange, Decimal("200.0"))
            await asyncio.wait_for(graph.wait_completion(), timeout=2.0)
            
        finally:
            await graph.stop()

    @pytest.mark.asyncio
    async def test_large_scale_random_topology_convergence(self) -> None:
        graph = Graph()
        await graph.start()
        
        try:
            exchange = MagicMock()
            num_nodes = 100
            coins = [MagicMock() for _ in range(num_nodes)]
            
            nodes = []
            for i in range(num_nodes):
                node = await graph.ensure_node(coins[i], exchange, Decimal("100.0"))
                nodes.append(node)
                
            random.seed(42)
            for i in range(num_nodes - 1):
                targets = random.sample(range(i + 1, num_nodes), min(3, num_nodes - 1 - i))
                for t in targets:
                    await graph.ensure_edge(nodes[i], nodes[t], Decimal("0.001"), Decimal("0.0"))
                    
            update_tasks = []
            for i in range(num_nodes - 10, num_nodes):
                update_tasks.append(graph.ensure_node(coins[i], exchange, Decimal("200.0")))
                
            await asyncio.gather(*update_tasks)
            await asyncio.wait_for(graph.wait_completion(), timeout=5.0)
            
        finally:
            await graph.stop()


class TestGraphStressAndResilience:
    @pytest.mark.asyncio
    async def test_stress_high_frequency_coalescing(self) -> None:
        graph = Graph()
        await graph.start()
        
        try:
            coin = MagicMock()
            exchange = MagicMock()
            
            await graph.ensure_node(coin, exchange, Decimal("100.0"))
            
            async def spam_updates(task_id: int) -> None:
                for i in range(500):
                    price = Decimal(str(100.0 + task_id + i * 0.001))
                    await graph.ensure_node(coin, exchange, price)
                    
            tasks = [spam_updates(i) for i in range(20)]
            await asyncio.gather(*tasks)
            
            await asyncio.wait_for(graph.wait_completion(), timeout=5.0)
            
        finally:
            await graph.stop()

    @pytest.mark.asyncio
    async def test_inter_exchange_transfer_anomaly_containment(self) -> None:
        graph = Graph()
        await graph.start()
        
        try:
            coin_btc_a, coin_btc_b = MagicMock(), MagicMock()
            exchange_a, exchange_b = MagicMock(), MagicMock()
            
            node_a = await graph.ensure_node(coin_btc_a, exchange_a, Decimal("50000.0"))
            node_b = await graph.ensure_node(coin_btc_b, exchange_b, Decimal("50000.0"))
            
            await graph.ensure_edge(node_a, node_b, Decimal("0.001"), Decimal("1.0"))
            
            await asyncio.wait_for(graph.wait_completion(), timeout=2.0)
            
            await graph.ensure_node(coin_btc_b, exchange_b, Decimal("51000.0"))
            await asyncio.wait_for(graph.wait_completion(), timeout=2.0)
            
            potential_a = node_a.get_potential()
            assert potential_a is not None
            assert potential_a.a > Decimal("1.0")
            
        finally:
            await graph.stop()