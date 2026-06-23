# План доработки существующего кода до рабочего состояния

## 🗂 Быстрая навигация по проекту

### Interfaces (Порты)
- [IAnalyst](src/application/interfaces/analyst.py)
- [IApi](src/application/interfaces/api.py)
- [IConnection](src/application/interfaces/connection.py)
- [IExchange](src/application/interfaces/exchange.py)
- [IManager](src/application/interfaces/manager.py)

### Core (Ядро)
- **Logic:** [Graph](src/core/logic/graph.py) • [Node](src/core/logic/node.py) • [Edge](src/core/logic/edge.py) • [Potential](src/core/logic/potential.py)
- **Entities:** [Asset](src/core/entities/asset.py) • [Coin](src/core/entities/coin.py) • [Deal](src/core/entities/deal.py) • [Exchange](src/core/entities/exchange.py) • [Ticker](src/core/entities/ticker.py) • [MarketInfo](src/core/entities/market_info.py)
- **DTO:** [RouteCandidate](src/core/dto/route_candidate.py)
- **Utils:** [AsyncRLock](src/core/utils/async_rlock.py)

### Infrastructure (Адаптеры)
- **Base:** [Analyst](src/infrastructure/base/analyst.py) • [Connection](src/infrastructure/base/connection.py) • [Exchange](src/infrastructure/base/exchange.py) • [Manager](src/infrastructure/base/manager.py)
- **Mocks:** [MockApi](src/infrastructure/mocks/api.py) • [MockConnection](src/infrastructure/mocks/connection.py) • [MockExchange](src/infrastructure/mocks/exchange.py)
- **CCXT:** [BitgetConnection](src/infrastructure/ccxt/bitget_connection.py)

### App & Visualizer
- [app.py](src/app.py)
- [GraphVisualizer](src/visualizer/graph_visualizer.py)

---

## Этап 1: Завершение математического ядра ([Graph](src/core/logic/graph.py) + тесты)
- [ ] Добавить метод `get_optimal_route(coin, exchange)` в [Graph](src/core/logic/graph.py) с использованием [AsyncRLock](src/core/utils/async_rlock.py)
- [ ] Добавить метод `get_best_deal(coin, exchange)` в [Graph](src/core/logic/graph.py) (обертка для [IAnalyst](src/application/interfaces/analyst.py))
- [ ] Написать unit-тест для [Potential](src/core/logic/potential.py): проверка лексикографического сравнения
- [ ] Написать unit-тест для [Edge](src/core/logic/edge.py): проверка формул пересчета с фиксированной комиссией
- [ ] Написать unit-тест для [Node](src/core/logic/node.py): проверка жадного выбора лучшего ребра
- [ ] Написать интеграционный тест для [Graph](src/core/logic/graph.py): создать 3 вершины, 2 ребра, запустить волну, проверить сходимость через `wait_completion()`
- [ ] Запустить тесты: `pytest tests/test_core_logic.py`

## Этап 2: Создание [Analyst](src/infrastructure/base/analyst.py) (обертка над [Graph](src/core/logic/graph.py))
- [ ] Создать файл [analyst.py](src/infrastructure/base/analyst.py)
- [ ] Реализовать класс `Analyst` с наследованием от [IAnalyst](src/application/interfaces/analyst.py)
- [ ] Добавить поле `self._graph` типа [Graph](src/core/logic/graph.py)
- [ ] Реализовать метод `get_best_deal(coin, exchange)` через вызов `Graph.get_best_deal()`
- [ ] Написать тест для `Analyst`: мокируем [Graph](src/core/logic/graph.py), проверяем delegation
- [ ] Запустить тесты: `pytest tests/test_analyst.py`

## Этап 3: Доработка [Exchange](src/infrastructure/base/exchange.py) (base)
- [ ] Добавить полную реализацию `launch(tg: TaskGroup)` в [Exchange](src/infrastructure/base/exchange.py)
- [ ] Добавить создание задач `run_balance_observer()` и `run_price_observer()` в `launch()`
- [ ] Добавить метод `stop()` с очисткой `self._working`
- [ ] Добавить обработку исключений в `run_balance_observer()` (логирование, retry)
- [ ] Добавить обработку исключений в `run_price_observer()` (логирование, retry)
- [ ] Написать тест для [Exchange](src/infrastructure/base/exchange.py) с [MockApi](src/infrastructure/mocks/api.py): проверить, что подписки работают
- [ ] Запустить тесты: `pytest tests/test_exchange.py`

## Этап 4: Создание [Manager](src/infrastructure/base/manager.py)
- [ ] Создать файл [manager.py](src/infrastructure/base/manager.py)
- [ ] Реализовать класс `Manager` с наследованием от [IManager](src/application/interfaces/manager.py)
- [ ] Добавить поле `self._exchange` типа [IExchange](src/application/interfaces/exchange.py)
- [ ] Добавить поле `self._analyst` типа [IAnalyst](src/application/interfaces/analyst.py)
- [ ] Добавить поле `self._coin_locks` типа `Dict[Coin, asyncio.Lock]` (где [Coin](src/core/entities/coin.py)) с `defaultdict(asyncio.Lock)`
- [ ] Реализовать метод `launch(tg: TaskGroup)` с созданием задачи `run_balance_observer()`
- [ ] Реализовать метод `run_balance_observer(coins: List[Coin])`, где [Coin](src/core/entities/coin.py)
- [ ] Реализовать метод `_evaluate_and_route(asset: Asset)` с захватом лока для монеты, где [Asset](src/core/entities/asset.py)
- [ ] Добавить заглушку метода `_is_transfer_feasible(asset, route)` (возвращает True)
- [ ] Реализовать метод `stop()`
- [ ] Написать тест для [Manager](src/infrastructure/base/manager.py): мокируем [IExchange](src/application/interfaces/exchange.py) и [IAnalyst](src/application/interfaces/analyst.py), проверяем, что при появлении баланса вызывается `get_best_deal()`
- [ ] Запустить тесты: `pytest tests/test_manager.py`

## Этап 5: Интеграция ([app.py](src/app.py))
- [ ] Обновить [app.py](src/app.py): добавить создание [Graph](src/core/logic/graph.py)
- [ ] Обновить [app.py](src/app.py): добавить вызов `Graph.start()`
- [ ] Обновить [app.py](src/app.py): добавить создание [Analyst](src/infrastructure/base/analyst.py) с инъекцией [Graph](src/core/logic/graph.py)
- [ ] Обновить [app.py](src/app.py): добавить создание [Manager](src/infrastructure/base/manager.py) с инъекцией [Exchange](src/infrastructure/base/exchange.py) и [Analyst](src/infrastructure/base/analyst.py)
- [ ] Обновить [app.py](src/app.py): добавить вызов `Manager.launch(tg)`
- [ ] Обновить [app.py](src/app.py): добавить вызов `Graph.stop()` в finally
- [ ] Написать end-to-end тест: запустить App с моками, проверить, что система не падает
- [ ] Запустить тесты: `pytest tests/test_integration.py`

## Этап 6: Доработка [Deal](src/core/entities/deal.py) и [RouteCandidate](src/core/dto/route_candidate.py)
- [ ] Добавить поле `route` типа `List[Node]` (где [Node](src/core/logic/node.py)) в [Deal](src/core/entities/deal.py)
- [ ] Добавить поле `multiplier: Decimal` в [Deal](src/core/entities/deal.py)
- [ ] Добавить поле `fixed_fee: Decimal` в [Deal](src/core/entities/deal.py)
- [ ] Обновить метод `get_best_deal()` в [Graph](src/core/logic/graph.py) для возврата заполненного [Deal](src/core/entities/deal.py)
- [ ] Написать тест: проверить, что [Deal](src/core/entities/deal.py) содержит корректный маршрут
- [ ] Запустить тесты: `pytest tests/test_deal.py`

## Этап 7: Исторические данные (опционально, для видео)
- [ ] Создать файл [historical_api.py](src/infrastructure/mocks/historical_api.py)
- [ ] Реализовать класс `HistoricalApi` с наследованием от [Api](src/application/interfaces/api.py)
- [ ] Добавить поле `self.db: AsyncSession`
- [ ] Добавить поле `self.model_time: datetime`
- [ ] Реализовать метод `fetch_ticker()` с SQL-запросом к market_telemetry
- [ ] Создать файл [historical_connection.py](src/infrastructure/mocks/historical_connection.py)
- [ ] Реализовать класс `HistoricalConnection` с наследованием от [Connection](src/application/interfaces/connection.py)
- [ ] Переопределить `_create_exchange_instance()` для возврата `HistoricalApi`
- [ ] Создать скрипт `scripts/record_telemetry.py` для записи данных в БД
- [ ] Написать тест: запустить систему на исторических данных, проверить сходимость волны
- [ ] Запустить тесты: `pytest tests/test_historical.py`

## Этап 8: Визуализация (для видео)
- [ ] Обновить [GraphVisualizer](src/visualizer/graph_visualizer.py): добавить метод `update_graph(graph)`, где `graph` — это [Graph](src/core/logic/graph.py)
- [ ] Добавить генерацию `graph.html` с PyVis
- [ ] Добавить раскраску узлов: красный если `potential.a > 1.01` (где [Potential](src/core/logic/potential.py))
- [ ] Добавить раскраску ребер: зеленый если `multiplier > 1.001`
- [ ] Добавить тултипы с `Potential(a, b)` (см. [Potential](src/core/logic/potential.py))
- [ ] Создать скрипт `scripts/visualize.py` для запуска визуализатора
- [ ] Протестировать: запустить визуализатор, открыть `graph.html` в браузере

## Этап 9: Финальная проверка
- [ ] Запустить все тесты: `pytest tests/`
- [ ] Запустить систему с моками: `python src/__main__.py`
- [ ] Проверить логи: нет ли необработанных исключений
- [ ] Проверить, что [Graph](src/core/logic/graph.py) корректно останавливается при Ctrl+C
- [ ] Записать видео для рецензента