from decimal import Decimal

import pytest

from src.core.entities.potential import Potential


class TestPotentialComparison:
    @pytest.mark.parametrize(
        "a1,b1,a2,b2,expected",
        [
            (Decimal("1.5"), Decimal("0.0"), Decimal("1.0"), Decimal("100.0"), True),
            (Decimal("2.0"), Decimal("-50.0"), Decimal("1.9"), Decimal("1000.0"), True),
            (Decimal("1.0"), Decimal("10.0"), Decimal("1.0"), Decimal("5.0"), True),
            (Decimal("1.0"), Decimal("0.0"), Decimal("1.0"), Decimal("0.0"), False),
            (Decimal("1.0"), Decimal("5.0"), Decimal("1.0"), Decimal("10.0"), False),
            (Decimal("0.5"), Decimal("100.0"), Decimal("1.0"), Decimal("-100.0"), False),
        ],
    )
    def test_lexicographical_greater_than(
        self, a1: Decimal, b1: Decimal, a2: Decimal, b2: Decimal, expected: bool
    ) -> None:
        potential1 = Potential(a=a1, b=b1)
        potential2 = Potential(a=a2, b=b2)
        assert (potential1 > potential2) is expected

    def test_less_than_operator(self) -> None:
        potential1 = Potential(a=Decimal("1.0"), b=Decimal("5.0"))
        potential2 = Potential(a=Decimal("1.0"), b=Decimal("10.0"))
        assert potential1 < potential2

    def test_equality_by_value(self) -> None:
        potential1 = Potential(a=Decimal("1.5"), b=Decimal("2.0"))
        potential2 = Potential(a=Decimal("1.5"), b=Decimal("2.0"))
        assert not (potential1 > potential2)
        assert not (potential2 > potential1)