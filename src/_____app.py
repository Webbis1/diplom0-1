import asyncio
import random
from decimal import Decimal
from typing import TYPE_CHECKING

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from streamlit_autorefresh import st_autorefresh

from core.entities import Coin, Exchange
from src.application.logic import Graph
from visualizer.graph_visualizer import GraphVisualizer

if TYPE_CHECKING:
    from src.application.logic import Node


st.set_page_config(page_title="Graph Visualizer", layout="wide")
st.title("Arbitrage Graph Visualizer")


@st.cache_resource
def get_graph() -> Graph:
    return Graph()


graph: Graph = get_graph()


async def populate_test_graph(target_graph: Graph) -> None:
    btc: Coin = Coin("BTC", "Bitcoin")
    eth: Coin = Coin("ETH", "Ethereum")
    usdt: Coin = Coin("USDT", "Tether")

    binance: Exchange = Exchange("Binance", {})
    coinbase: Exchange = Exchange("Coinbase", {})
    kraken: Exchange = Exchange("Kraken", {})

    await target_graph.ensure_node(btc, binance, Decimal("60000"))
    await target_graph.ensure_node(btc, coinbase, Decimal("60100"))
    await target_graph.ensure_node(btc, kraken, Decimal("59900"))

    await target_graph.ensure_node(eth, binance, Decimal("3000"))
    await target_graph.ensure_node(eth, coinbase, Decimal("3010"))

    await target_graph.ensure_node(usdt, binance, Decimal("1"))
    await target_graph.ensure_node(usdt, coinbase, Decimal("1"))
    await target_graph.ensure_node(usdt, kraken, Decimal("1"))

    nodes_snapshot: list[tuple[Coin, Exchange]] = [
        (btc, binance), (btc, coinbase), (btc, kraken),
        (eth, binance), (eth, coinbase),
        (usdt, binance), (usdt, coinbase), (usdt, kraken),
    ]

    node_map: dict[tuple[Coin, Exchange], Node] = {}
    for coin, ex in nodes_snapshot:
        node_map[(coin, ex)] = await target_graph.ensure_node(coin, ex, Decimal("1"))

    target_graph.ensure_edge(node_map[(btc, binance)], node_map[(usdt, binance)], Decimal("60000"), Decimal("10"))
    target_graph.ensure_edge(node_map[(btc, coinbase)], node_map[(usdt, coinbase)], Decimal("60100"), Decimal("15"))
    target_graph.ensure_edge(node_map[(btc, kraken)], node_map[(usdt, kraken)], Decimal("59900"), Decimal("12"))

    target_graph.ensure_edge(node_map[(eth, binance)], node_map[(usdt, binance)], Decimal("3000"), Decimal("5"))
    target_graph.ensure_edge(node_map[(eth, coinbase)], node_map[(usdt, coinbase)], Decimal("3010"), Decimal("8"))

    target_graph.ensure_edge(node_map[(usdt, binance)], node_map[(btc, binance)], Decimal("0.0000167"), Decimal("5"))
    target_graph.ensure_edge(node_map[(usdt, binance)], node_map[(eth, binance)], Decimal("0.000333"), Decimal("5"))

    target_graph.ensure_edge(node_map[(usdt, coinbase)], node_map[(btc, coinbase)], Decimal("0.0000166"), Decimal("8"))
    target_graph.ensure_edge(node_map[(usdt, coinbase)], node_map[(eth, coinbase)], Decimal("0.000332"), Decimal("8"))

    target_graph.ensure_edge(node_map[(btc, binance)], node_map[(btc, coinbase)], Decimal("1.001"), Decimal("20"))
    target_graph.ensure_edge(node_map[(btc, coinbase)], node_map[(btc, kraken)], Decimal("1.002"), Decimal("25"))

    target_graph.ensure_edge(node_map[(eth, binance)], node_map[(eth, coinbase)], Decimal("1.001"), Decimal("10"))

    await target_graph.start()


async def price_simulator(target_graph: Graph) -> None:
    coins: list[Coin] = [Coin("BTC", "Bitcoin"), Coin("ETH", "Ethereum"), Coin("USDT", "Tether")]
    exchanges: list[Exchange] = [Exchange("Binance", {}), Exchange("Coinbase", {}), Exchange("Kraken", {})]

    base_prices: dict[tuple[str, str], Decimal] = {
        ("BTC", "Binance"): Decimal("60000"),
        ("BTC", "Coinbase"): Decimal("60100"),
        ("BTC", "Kraken"): Decimal("59900"),
        ("ETH", "Binance"): Decimal("3000"),
        ("ETH", "Coinbase"): Decimal("3010"),
        ("USDT", "Binance"): Decimal("1"),
        ("USDT", "Coinbase"): Decimal("1"),
        ("USDT", "Kraken"): Decimal("1"),
    }

    while True:
        await asyncio.sleep(3)
        coin: Coin = random.choice(coins)
        exchange: Exchange = random.choice(exchanges)
        key: tuple[str, str] = (coin.symbol, exchange.name)
        base: Decimal | None = base_prices.get(key)
        if base is None:
            continue
        shift: Decimal = base * Decimal(str(random.uniform(-0.005, 0.005)))
        new_price: Decimal = base + shift
        await target_graph.ensure_node(coin, exchange, new_price)

asyncio.run(populate_test_graph(graph))

async def init_graph() -> None:
    asyncio.create_task(price_simulator(graph))


try:
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    if not loop.is_running():
        loop.run_until_complete(init_graph())
except RuntimeError:
    asyncio.run(init_graph())

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