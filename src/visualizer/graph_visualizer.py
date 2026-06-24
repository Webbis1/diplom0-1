from __future__ import annotations
from pyvis.network import Network
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..application.logic.graph import Graph
    from ..application.logic.node import Node
    from ..core.entities import Coin
    from ..core.entities import Exchange


class GraphVisualizer:
    def __init__(self, graph: Graph) -> None:
        self.__graph: Graph = graph

    def to_pyvis(self) -> Network:
        net: Network = Network(directed=True, notebook=True, height="750px")
        net.toggle_physics(True)
        net.barnes_hut(gravity=-80000, spring_length=250, spring_strength=0.001)

        node_mapping: dict[Node, int] = {}

        for coin, exchange_dict in self.__graph.nodes.items():
            for ex, node in exchange_dict.items():
                if node in node_mapping:
                    continue
                vis_id: int = len(node_mapping)
                node_mapping[node] = vis_id

                label: str = f"{coin.symbol}\\n{ex.name}"
                potential_a: float = float(node.get_potential().a)
                potential_b: float = float(node.get_potential().b)
                price: float = float(node.get_price())

                title: str = (
                    f"Node: {coin.symbol} @ {ex.name}\\n"
                    f"Price: {price}\\n"
                    f"Potential: {potential_a:.4f}x + {potential_b:.4f}"
                )

                color: str = "#97c2fc"
                if potential_a > 1.01:
                    color = "#ff9999"

                net.add_node(
                    vis_id,
                    label=label,
                    title=title,
                    color=color,
                    value=max(1.0, potential_a * 5)
                )

        for source, targets in self.__graph.edges.items():
            if source not in node_mapping:
                continue
            source_id: int = node_mapping[source]

            for target, edge in targets.items():
                if target not in node_mapping:
                    continue
                target_id: int = node_mapping[target]

                multiplier: float = float(edge.multiplier)
                fixed_fee: float = float(edge.get_fixed_fee())

                edge_title: str = (
                    f"Mult: {multiplier:.6f}\\n"
                    f"Fee: {fixed_fee}"
                )

                edge_color: str = "#848484"
                if multiplier > 1.001:
                    edge_color = "#27ae60"

                net.add_edge(
                    source_id,
                    target_id,
                    value=multiplier,
                    title=edge_title,
                    color=edge_color,
                    arrows="to"
                )

        return net

    def to_html(self, filename: str = "graph.html") -> str:
        net: Network = self.to_pyvis()
        net.repulsion(node_distance=220, spring_length=200)
        net.write_html(filename)
        return filename

    def get_profitable_paths(self) -> list[dict[str, object]]:
        paths: list[dict[str, object]] = []
        for ex_node in self.__graph.nodes.values():
            for node in ex_node.values():
                potential_a: float = float(node.get_potential().a)
                if potential_a > 1.001:
                    path_ids: list[int] = list(node.get_potential().path)
                    path_data: dict[str, object] = {
                        "node": node,
                        "potential_a": potential_a,
                        "path_length": len(path_ids)
                    }
                    paths.append(path_data)
        return paths