from abc import ABC, abstractmethod
from asyncio import Event, Lock, TaskGroup
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from ccxt.pro import Exchange as CcxtProExchange

import asyncio
import logging
import math
import aiohttp
import ccxt

from src.application.interfaces import Api

class Connection(ABC):
    def __init__(self, name: str, tg: TaskGroup) -> None:
        self.name: str = name
        
        self.tg: TaskGroup = tg
        self.__retry_count_limit: int = 5
        self.__launch_time: float = 0
        
        self.__instance: "Api | None"        
        self.__working: Event = Event()
        self.__disabled: Event = Event()
        self.__connected: Event = Event()
        self.__is_shutdown: Event = Event()
        self.__reconnection_is_underway: Event = Event()

        self._reconnect_lock: Lock = Lock()
        self.__connection_lock: Lock = Lock()

        self.__disabled.set()
        
    @property
    def logger(self):
        return logging.getLogger(f'CCXT_Connection for {self.name}')
    
    @property
    def connected(self) -> bool:
        """Есть подключение?"""
        return self.__connected.is_set()
    
    @property
    def working(self) -> bool:
        """Работаем?"""
        return self.__working.is_set()
    
    @property
    def reconnecting(self) -> bool:
        return self.__reconnection_is_underway.is_set()
    
    def stop(self, reason = None):
        self.__working.clear()
        self.__disabled.set()
    
    async def launch(self):
        self.__working.set()
        self.__disabled.clear()
        await self.connection()
    
    @abstractmethod
    def _create_exchange_instance(self) -> Api: ...

    async def connection(self):
        if not self.working or self.connected: return

        base_delay = 1
        max_delay = 60
        retry_count: int = 0
        
        while retry_count < self.__retry_count_limit and self.working:
            async with self.__connection_lock:
                if self.connected: #TODO
                    break

                try:
                    self.__instance = self._create_exchange_instance()
                    
                    await asyncio.wait_for(self.__instance.load_markets(), timeout=30.0)
                    
                    self.logger.warning(f"Successfully connected to {self.name} and loaded markets.")

    
                    self.__connected.set()
                    self.__is_shutdown.clear()
                    self.tg.create_task(self.__shutdown_watcher())
                    return
                    
                except (ccxt.AuthenticationError, ccxt.PermissionDenied, ccxt.AccountSuspended) as e:
                    self.logger.critical(f"Critical auth error: {e}")
                    self.stop("Couldn't connect")
                    return
                    
                except ccxt.DDoSProtection as e:
                    ddos_delay = getattr(e, 'retry_after', delay * 3)
                    self.logger.warning(f"DDoS protection, waiting {ddos_delay}s")
                    await asyncio.sleep(ddos_delay)
                    continue
                    
                except ccxt.OnMaintenance as e:
                    self.logger.warning("Exchange under maintenance, waiting 5 minutes")
                    await asyncio.sleep(300)
                    continue
                    
                except ccxt.RateLimitExceeded as e:
                    rate_delay = getattr(e, 'retry_after', delay * 2)
                    self.logger.warning(f"Rate limit exceeded, waiting {rate_delay}s")
                    await asyncio.sleep(rate_delay)
                    continue
                    
                except (asyncio.TimeoutError, ccxt.RequestTimeout, ccxt.NetworkError, 
                        ccxt.ExchangeNotAvailable, aiohttp.ClientConnectorError,
                        aiohttp.ServerDisconnectedError, ConnectionError, 
                        ConnectionRefusedError) as e:
                    self.logger.warning(f"Connection attempt {retry_count} failed: {type(e).__name__}")
                    continue
                    
                except ccxt.ExchangeError as e:
                    if 'maintenance' in str(e).lower():
                        self.logger.warning("Exchange maintenance detected, waiting 5 minutes")
                        await asyncio.sleep(300)
                        continue
                    else:
                        self.logger.error(f"Exchange error: {e}")
                        continue
                
                except asyncio.CancelledError:
                    self.logger.debug("connection was cancelled")
                    self.stop("Couldn't connect")
                    return        
                
                except Exception as e:
                    self.logger.error(f"Unexpected error: {e}")
                    continue
        
            delay = min(base_delay * (2 ** retry_count), max_delay)
            await asyncio.sleep(delay)
            retry_count += 1
        
        else:
            self.stop("Couldn't connect")
    
    async def __reconnecting(self):
        if self.reconnecting or not self.working:
            return
        
        self.__reconnection_is_underway.set()
        
        try:
            current_delay = 5
            await asyncio.sleep(current_delay)
            while self.working:
                async with self._reconnect_lock:
                    current_time = asyncio.get_event_loop().time()
                    if current_time >= self.__launch_time:
                        break
                    current_delay = math.ceil(self.__launch_time - current_time)
                await asyncio.sleep(current_delay)
            
            await self.connection()
        
        except asyncio.CancelledError:
            self.logger.debug("__reconnecting was cancelled")
            return
          
        finally:
            self.__reconnection_is_underway.clear()
    
    async def __shutdown_watcher(self):
        try:
            shutdown_task = asyncio.create_task(self.__is_shutdown.wait())
            running_task = asyncio.create_task(self.__disabled.wait())
            timeout_task = asyncio.create_task(asyncio.sleep(24 * 60 * 60))  # 24 часа
            
            done, pending = await asyncio.wait(
                [shutdown_task, running_task, timeout_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
                
            if shutdown_task in done:
                await self.__reconnecting()
                self.logger.info("Shutdown signal received")
            
            elif running_task in done:
                self.logger.info("Running state changed")
                await self.disconnect()
                await asyncio.sleep(1)
                self.logger.info("Corretly finish")
            
            elif timeout_task in done:
                self.logger.warning("24-hour timeout reached, reconnecting...")
                await self.disconnect()
                await self.__reconnecting()
                self.logger.info("Reconnection after timeout completed")
                
        except asyncio.CancelledError:
            self.logger.info("Shutdown watcher was cancelled")
            await asyncio.shield(self.disconnect())
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in shutdown watcher: {e}")
            await self.disconnect()
            await self.__reconnecting()
    
    async def wait_ready(self) -> bool:
        status: bool = False
        try:
            connected_task = asyncio.create_task(self.__connected.wait())
            running_task = asyncio.create_task(self.__disabled.wait())
            
            done, pending = await asyncio.wait(
                [connected_task, running_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            if connected_task in done:
                status = True
                
        except asyncio.CancelledError:
            self.logger.info("wait_ready was cancelled")
        except Exception as e:
            self.logger.error(f"Unexpected error in wait_ready: {e}")
        finally:
            return status
    
    async def disconnect(self):
        async with self.__connection_lock:
            if not self.connected:
                return 
            
            if self.__instance:
                try:
                    self.logger.info("Starting exchange close process...")

                    try:
                        await asyncio.wait_for(self.__instance.close(), timeout=5.0)
                        self.logger.info("Successfully closed exchange")
                    except asyncio.TimeoutError:
                        self.logger.warning("Exchange close timed out, forcing closure")
                    except Exception as e:
                        self.logger.warning(f"Error during exchange close: {e}")
                    except asyncio.CancelledError:
                        self.logger.critical("Disconnection was cancelled")
                    finally:
                        self.logger.info("Finally closed exchange")
                    
                    # await asyncio.sleep(1.0)
                    
                except Exception as e:
                    self.logger.warning(f"Unexpected error during close: {e}")
                finally:
                    self.__instance = None

            
            self.__connected.clear()

        

    
    
    
    
    

    @asynccontextmanager
    async def client(self) -> AsyncIterator["Api"]:            
        await self.__connected.wait()
        try:
            yield self.__instance
            
            
        except (ccxt.DDoSProtection, ccxt.OnMaintenance, ccxt.ExchangeNotAvailable,
                ccxt.RequestTimeout, asyncio.TimeoutError, ConnectionError,
                aiohttp.ServerDisconnectedError, ccxt.NetworkError) as e:
            self.logger.warning({type(e).__name__})
            await self.disconnect()
            await self.__update_last_exception(e)
            
            
            self.__is_shutdown.set()
            # yield None
        
        except asyncio.CancelledError:
            self.logger.critical("connection was cancelled")
            self.stop()
            raise
        
        except ccxt.AuthenticationError as e:
            self.logger.critical(f"AuthenticationError")
            self.stop()

    
        finally:
            self.logger.info("Close contextmanager")
            
            
            
    async def __update_last_exception(self, last_excpetion: Exception):
        """Обновляет время переподключения в зависимости от типа ошибки"""
        delay = self.__get_retry_delay(last_excpetion)
        async with self._reconnect_lock:
            current_time = asyncio.get_event_loop().time()
            target_time = current_time + delay
            
            if self.__launch_time < target_time:
                self.__launch_time = target_time
                
                
    def __get_retry_delay(self, error: Exception) -> int:
        """Определяет задержку повтора в зависимости от типа ошибки"""
        error_delays = {
            ccxt.DDoSProtection: 60,
            ccxt.OnMaintenance: 300,
            ccxt.ExchangeNotAvailable: 30,
            ccxt.RequestTimeout: 2,
            asyncio.TimeoutError: 2,
            ConnectionError: 10,
            aiohttp.ServerDisconnectedError: 10,
            ccxt.NetworkError: 5,
        }
        
        for error_type, delay in error_delays.items():
            if isinstance(error, error_type):
                return delay
        
        return 5
    