from asyncio import TaskGroup
import asyncio
import logging

from .application.interfaces import Connection

from src.infrastructure.mocks import MockApi, Exchange

from .infrastructure.ccxt.bitget_connection import BitgetConnection

class App:
    def __init__(self) -> None:
        self._tg: TaskGroup = TaskGroup()
        
    @property
    def __logger(self):
        return logging.getLogger("App")    
        
    async def launch(self):
        try:
            async with self._tg as tg:
                self.__logger.info("Launch system")
                
                conn: Connection = BitgetConnection("test", tg)
                
                tg.create_task(conn.launch())
                
                ex: Exchange = Exchange("test", conn)
                
                await ex.launch(tg)
                

                
                
        except asyncio.CancelledError:
            self.__logger.warning("Главная задача системы была отменена.")
        finally:
            self.__logger.info("Финальная очистка ресурсов системы завершена.")
        