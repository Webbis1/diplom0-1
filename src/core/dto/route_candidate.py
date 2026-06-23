from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from bitarray import bitarray

if TYPE_CHECKING:
    from src.core.logic.edge import Edge
    from src.core.logic.node import Node


@dataclass(frozen=True)
class RouteCandidate:
    departure: Node
    destination: Node
    edge: Edge
    multiplier: Decimal
    residual_value: Decimal
    path: bitarray