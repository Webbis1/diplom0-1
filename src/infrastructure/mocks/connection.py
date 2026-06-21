from ..base.connection import Connection as BaseConnection
from .api import MockApi as Api


class Connection(BaseConnection):
    def _create_exchange_instance(self) -> Api:
        return Api()