import logging

from ..base import Exchange as BaseEchange
from src.application.interfaces import Api


class Exchange(BaseEchange):
    
    @property
    def __logger(self):
        return logging.getLogger(f'MocksExchange for {self.name}')
    
    
    async def _balance_request(self, api: "Api"):
        balance = await api.watch_balance()
        self.__logger.info(balance)
        
        
    
    async def _price_request(self, api: "Api"):
        ticker = await api.watch_ticker("usdt")
        self.__logger.info(ticker)