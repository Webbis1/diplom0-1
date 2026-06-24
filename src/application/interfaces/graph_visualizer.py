from typing import Protocol

from ..logic.graph import Graph


class IGraphVisualizer(Protocol):
    async def render(self, graph: Graph) -> None: ...