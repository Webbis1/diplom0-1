from ..base import Connection
from src.application.interfaces import Api

import ccxt

class BitgetConnection(Connection):
    def _create_exchange_instance(self) -> Api:
        exchange = ccxt.bitget({
            'apiKey': 'bg_762cfdffe1518b09ba3a11a80f38124a',
            'secret': '194c44935a26fcab8707f97e0d370229a31038818c54aacfbcdc03b9d6c548ab',
            'password': 'cnkjnacs89w',
            'options': {
                'defaultType': 'spot',
            }
        })
        return exchange