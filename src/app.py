import asyncio
from decimal import Decimal
import logging
from asyncio import TaskGroup

from src.infrastructure.base.analyst import Analyst
# from src.infrastructure.base.exchange import Exchange
from src.infrastructure.mocks import MockExchange as Exchange, Connection
from src.core.entities import Exchange as ExchangeInfo


class App:
    def __init__(self) -> None:
        self._tg: TaskGroup = TaskGroup()
        
    @property
    def __logger(self) -> logging.Logger:
        return logging.getLogger("App")    
        
    async def launch(self) -> None:
        try:
            async with self._tg as tg:
                self.__logger.info("Запуск системы арбитража")
                
                # Создаем подключения к биржам
                connections = [
                    Connection("bitget", tg),
                    Connection("binance", tg),
                    Connection("bybit", tg),
                    Connection("htx", tg),
                    Connection("kucoin", tg),
                    Connection("mexc", tg),
                ]
                
                # Запускаем все подключения
                for conn in connections:
                    await conn.launch()
                
                # Создаем биржи
                exchanges: list[Exchange] = []
                for conn in connections:
                    if not conn.connected:
                        continue
                    exchange_info = ExchangeInfo(
                        name=conn.name,
                        address_list={}
                    )
                    exchange = Exchange(exchange_info, conn)
                    await exchange.launch(tg)
                    exchanges.append(exchange)
                
                # Создаем и запускаем аналитика
                analyst = Analyst(exchanges)
                await analyst.launch(tg)
                
                self.__logger.info(f"Система запущена. Бирж: {len(exchanges)}")
                
                # Держим приложение запущенным
                while True:
                    await asyncio.sleep(1)
                    if len(exchanges) > 0:
                        ex = exchanges[0]
                        coins = await ex.get_available_coins()
                        if len(coins) > 0:
                            route = await analyst.get_optimal_route(coins[0], ex)
                            if route and route.multiplier > Decimal("1"):
                                self.__logger.info(route)
                    
        except asyncio.CancelledError:
            self.__logger.warning("Главная задача системы была отменена.")
        except Exception as e:
            self.__logger.error(f"Критическая ошибка в системе: {type(e).__name__}: {e}")
            raise
        finally:
            self.__logger.info("Финальная очистка ресурсов системы завершена.")