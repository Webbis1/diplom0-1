from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.core.logic.node import Node
from src.core.logic.potential import Potential


class FakeEdge:
    def __init__(self, potential: Potential) -> None:
        self._potential = potential

    def get_potential(self) -> Potential:
        return self._potential

    def __gt__(self, other: "FakeEdge") -> bool:
        return self._potential > other._potential


class TestNodeGreedySelection:
    def test_selects_edge_with_highest_multiplier(self) -> None:
        node = Node(price_to_usdt=Decimal("100.0"), node_id=1)
        
        edge1 = FakeEdge(Potential(a=Decimal("1.05"), b=Decimal("10.0")))
        edge2 = FakeEdge(Potential(a=Decimal("1.10"), b=Decimal("5.0")))
        edge3 = FakeEdge(Potential(a=Decimal("1.02"), b=Decimal("20.0")))
        
        node.add_outgoing_edge(edge1)
        node.add_outgoing_edge(edge2)
        node.add_outgoing_edge(edge3)
        
        incoming_edges = node.update()
        
        assert node.get_potential().a == Decimal("1.10")
        assert node.get_potential().b == Decimal("5.0")
        assert incoming_edges is not None

    def test_selects_edge_with_higher_b_when_a_is_equal(self) -> None:
        node = Node(price_to_usdt=Decimal("100.0"), node_id=1)
        
        edge1 = FakeEdge(Potential(a=Decimal("1.05"), b=Decimal("10.0")))
        edge2 = FakeEdge(Potential(a=Decimal("1.05"), b=Decimal("15.0")))
        
        node.add_outgoing_edge(edge1)
        node.add_outgoing_edge(edge2)
        
        incoming_edges = node.update()
        
        assert node.get_potential().a == Decimal("1.05")
        assert node.get_potential().b == Decimal("15.0")

    def test_no_update_when_best_edge_is_worse_than_current(self) -> None:
        node = Node(price_to_usdt=Decimal("100.0"), node_id=1)
        node._Node__potential = Potential(a=Decimal("1.20"), b=Decimal("20.0"))
        
        edge1 = FakeEdge(Potential(a=Decimal("1.05"), b=Decimal("10.0")))
        node.add_outgoing_edge(edge1)
        
        incoming_edges = node.update()
        
        assert node.get_potential().a == Decimal("1.20")
        assert node.get_potential().b == Decimal("20.0")
        assert incoming_edges is None

    def test_returns_incoming_edges_on_successful_update(self) -> None:
        node = Node(price_to_usdt=Decimal("100.0"), node_id=1)
        
        incoming_edge1 = MagicMock()
        incoming_edge2 = MagicMock()
        node.add_incoming_edge(incoming_edge1)
        node.add_incoming_edge(incoming_edge2)
        
        outgoing_edge = FakeEdge(Potential(a=Decimal("1.10"), b=Decimal("10.0")))
        node.add_outgoing_edge(outgoing_edge)
        
        result = node.update()
        
        assert result is not None
        assert len(result) == 2
        assert incoming_edge1 in result
        assert incoming_edge2 in result

    def test_no_outgoing_edges_returns_none(self) -> None:
        node = Node(price_to_usdt=Decimal("100.0"), node_id=1)
        
        result = node.update()
        
        assert result is None