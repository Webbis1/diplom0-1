from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.core.logic.edge import Edge
from src.core.logic.potential import Potential


class TestEdgeCalculatePotential:
    @pytest.mark.parametrize(
        "incoming_a,incoming_b,multiplier,fixed_fee,expected_a,expected_b",
        [
            (Decimal("1.0"), Decimal("100.0"), Decimal("1.05"), Decimal("2.0"), Decimal("1.05"), Decimal("97.9")),
            (Decimal("2.0"), Decimal("50.0"), Decimal("1.10"), Decimal("1.0"), Decimal("2.2"), Decimal("47.8")),
            (Decimal("1.5"), Decimal("10.0"), Decimal("1.02"), Decimal("5.5"), Decimal("1.53"), Decimal("1.585")),
            (Decimal("1.2"), Decimal("0.0"), Decimal("1.5"), Decimal("0.1"), Decimal("1.8"), Decimal("-0.18")),
        ],
    )
    def test_affine_transformation(
        self,
        incoming_a: Decimal,
        incoming_b: Decimal,
        multiplier: Decimal,
        fixed_fee: Decimal,
        expected_a: Decimal,
        expected_b: Decimal,
    ) -> None:
        mock_departure = MagicMock()
        mock_departure.get_id.return_value = 1
        mock_destination = MagicMock()
        
        edge = Edge(
            departure=mock_departure,
            destination=mock_destination,
            commission=Decimal("0.001"),
            fixed_fee=fixed_fee,
        )
        
        incoming_potential = Potential(a=incoming_a, b=incoming_b)
        
        with patch.object(Edge, "multiplier", new_callable=PropertyMock) as mock_mult:
            mock_mult.return_value = multiplier
            result = edge.calculate_potential(incoming_potential)
        
        assert result is not None
        assert result.a == expected_a
        assert result.b == expected_b

    def test_topological_barrier_blocks_propagation(self) -> None:
        mock_departure = MagicMock()
        mock_departure.get_id.return_value = 1
        mock_destination = MagicMock()
        
        edge = Edge(
            departure=mock_departure,
            destination=mock_destination,
            commission=Decimal("0.001"),
            fixed_fee=Decimal("0.0"),
        )
        incoming_potential = Potential(a=Decimal("1.0"), b=Decimal("10.0"))
        
        with patch.object(Edge, "multiplier", new_callable=PropertyMock) as mock_mult:
            mock_mult.return_value = Decimal("0.9")
            result = edge.calculate_potential(incoming_potential)
        
        assert result is None

    def test_barrier_triggers_on_exact_one(self) -> None:
        mock_departure = MagicMock()
        mock_departure.get_id.return_value = 1
        mock_destination = MagicMock()
        
        edge = Edge(
            departure=mock_departure,
            destination=mock_destination,
            commission=Decimal("0.001"),
            fixed_fee=Decimal("0.0"),
        )
        incoming_potential = Potential(a=Decimal("1.0"), b=Decimal("10.0"))
        
        with patch.object(Edge, "multiplier", new_callable=PropertyMock) as mock_mult:
            mock_mult.return_value = Decimal("1.0")
            result = edge.calculate_potential(incoming_potential)
        
        assert result is None

    def test_fee_exceeds_residual_value(self) -> None:
        mock_departure = MagicMock()
        mock_departure.get_id.return_value = 1
        mock_destination = MagicMock()
        
        edge = Edge(
            departure=mock_departure,
            destination=mock_destination,
            commission=Decimal("0.001"),
            fixed_fee=Decimal("50.0"),
        )
        incoming_potential = Potential(a=Decimal("1.0"), b=Decimal("10.0"))
        
        with patch.object(Edge, "multiplier", new_callable=PropertyMock) as mock_mult:
            mock_mult.return_value = Decimal("1.5")
            result = edge.calculate_potential(incoming_potential)
        
        assert result is not None
        assert result.b == Decimal("-65.0")


class TestEdgeMultiplierProperty:
    def test_multiplier_with_fixed_fee(self) -> None:
        mock_departure = MagicMock()
        mock_departure.get_price.return_value = Decimal("100.0")
        mock_destination = MagicMock()
        mock_destination.get_price.return_value = Decimal("110.0")
        
        edge = Edge(
            departure=mock_departure,
            destination=mock_destination,
            commission=Decimal("0.01"),
            fixed_fee=Decimal("1.0"),
        )
        
        assert edge.multiplier == Decimal("0.99") * (Decimal("110.0") / Decimal("100.0"))

    def test_multiplier_without_fixed_fee(self) -> None:
        mock_departure = MagicMock()
        mock_departure.get_price.return_value = Decimal("100.0")
        mock_destination = MagicMock()
        mock_destination.get_price.return_value = Decimal("110.0")
        
        edge = Edge(
            departure=mock_departure,
            destination=mock_destination,
            commission=Decimal("0.01"),
            fixed_fee=Decimal("0.0"),
        )
        
        assert edge.multiplier == Decimal("0.99")