from decimal import Decimal
from typing import TYPE_CHECKING
from core.logic import Graph
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from pyvis.network import Network
from visualizer.graph_visualizer import GraphVisualizer
from core.entities import Coin, Exchange
import streamlit.components.v1 as components

if TYPE_CHECKING:
    from core.logic import Node


st.set_page_config(page_title="Graph Visualizer", layout="wide")
st.title("Arbitrage Graph Visualizer")


@st.cache_resource
def get_graph() -> "Graph":
    return Graph()




graph: Graph = get_graph()

def populate_test_graph(graph: Graph) -> None:
    btc: Coin = Coin("BTC", "Bitcoin")
    eth: Coin = Coin("ETH", "Ethereum")
    usdt: Coin = Coin("USDT", "Tether")
    
    binance: Exchange = Exchange("Binance", {})
    coinbase: Exchange = Exchange("Coinbase", {})
    kraken: Exchange = Exchange("Kraken", {})
    
    btc_binance: Node = graph.ensure_node(btc, binance, Decimal("60000"))
    btc_coinbase: Node = graph.ensure_node(btc, coinbase, Decimal("60100"))
    btc_kraken: Node = graph.ensure_node(btc, kraken, Decimal("59900"))
    
    eth_binance: Node = graph.ensure_node(eth, binance, Decimal("3000"))
    eth_coinbase: Node = graph.ensure_node(eth, coinbase, Decimal("3010"))
    
    usdt_binance: Node = graph.ensure_node(usdt, binance, Decimal("1"))
    usdt_coinbase: Node = graph.ensure_node(usdt, coinbase, Decimal("1"))
    usdt_kraken: Node = graph.ensure_node(usdt, kraken, Decimal("1"))
    
    graph.ensure_edge(btc_binance, usdt_binance, 60000.0, 10.0)
    graph.ensure_edge(btc_coinbase, usdt_coinbase, 60100.0, 15.0)
    graph.ensure_edge(btc_kraken, usdt_kraken, 59900.0, 12.0)
    
    graph.ensure_edge(eth_binance, usdt_binance, 3000.0, 5.0)
    graph.ensure_edge(eth_coinbase, usdt_coinbase, 3010.0, 8.0)
    
    graph.ensure_edge(usdt_binance, btc_binance, 0.0000167, 5.0)
    graph.ensure_edge(usdt_binance, eth_binance, 0.000333, 5.0)
    
    graph.ensure_edge(usdt_coinbase, btc_coinbase, 0.0000166, 8.0)
    graph.ensure_edge(usdt_coinbase, eth_coinbase, 0.000332, 8.0)
    
    graph.ensure_edge(btc_binance, btc_coinbase, 1.001, 20.0)
    graph.ensure_edge(btc_coinbase, btc_kraken, 1.002, 25.0)
    
    graph.ensure_edge(eth_binance, eth_coinbase, 1.001, 10.0)


populate_test_graph(graph)

visualizer: GraphVisualizer = GraphVisualizer(graph)



count = st_autorefresh(interval=2000, key="datarefresh")

tab1, tab2 = st.tabs(["Граф", "Выгодные пути"])

with tab1:
    net: Network = visualizer.to_pyvis()
    html: str = net.generate_html()
    components.html(html, height=800, scrolling=True)

with tab2:
    paths = visualizer.get_profitable_paths()
    if not paths:
        st.info("Выгодных путей пока не найдено")
    else:
        for path_info in paths:
            st.metric(
                label=f"Node {path_info['node'].get_id()}",
                value=f"x{path_info['potential_a']:.4f}",
                delta=f"Path length: {path_info['path_length']}"
            )