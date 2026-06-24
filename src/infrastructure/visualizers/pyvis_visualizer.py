import logging
import time

from pyvis.network import Network

from src.application.interfaces.graph_visualizer import IGraphVisualizer
from src.application.logic.graph import Graph
from src.application.logic.node import Node


class PyvisVisualizer:
    def __init__(self, output_path: str = "arbitrage_graph.html", throttle: float = 1.0) -> None:
        self._output_path: str = output_path
        self._throttle: float = throttle
        self._last_render: float = 0.0
        self._color_palette: list[str] = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
            "#98D8C8", "#F7DC6F", "#C39BD3", "#85C1E2",
        ]

    @property
    def __logger(self) -> logging.Logger:
        return logging.getLogger("PyvisVisualizer")

    async def render(self, graph: Graph) -> None:
        now: float = time.time()
        if now - self._last_render < self._throttle:
            return
        self._last_render = now

        net: Network = Network(height="900px", width="100%", directed=True, notebook=False)
        net.toggle_physics(True)

        node_to_id: dict[Node, str] = {}
        exchange_colors: dict[str, str] = {}

        for coin, exchanges in graph.nodes.items():
            for ex, node in exchanges.items():
                if ex.name not in exchange_colors:
                    exchange_colors[ex.name] = self._color_palette[
                        len(exchange_colors) % len(self._color_palette)
                    ]

                nid: str = f"{coin.symbol}@{ex.name}"
                node_to_id[node] = nid

                pot = node.get_potential()
                label: str = f"{coin.symbol}@{ex.name}\nP:{pot.a:.4f}"
                title: str = f"Price: {node.get_price()}\nPotential a: {pot.a:.6f}\nResidual: {pot.b:.6f}"

                net.add_node(
                    nid,
                    label=label,
                    color=exchange_colors[ex.name],
                    size=25,
                    title=title,
                )

        for dep, destinations in graph.edges.items():
            for dest, edge in destinations.items():
                if dep not in node_to_id or dest not in node_to_id:
                    continue

                pot = edge.get_potential()
                mult: float = float(pot.a)
                width: float = max(1.0, min(12.0, mult * 4))
                color: str = "#2ECC71" if mult > 1.0 else "#E74C3C"

                net.add_edge(
                    node_to_id[dep],
                    node_to_id[dest],
                    value=width,
                    color=color,
                    title=(
                        f"Mult: {mult:.6f}\n"
                        f"Commission: {edge.multiplier}\n"
                        f"Fixed fee: {edge.get_fixed_fee()}\n"
                        f"Residual: {pot.b:.6f}"
                    ),
                    label=f"{mult:.4f}",
                )

        try:
            net.write_html(self._output_path, notebook=False)
        except Exception as e:
            self.__logger.error(f"Render failed: {e}")