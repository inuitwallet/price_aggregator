import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


class Cryptonator(object):
    """
    https://www.cryptonator.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Cryptonator: Getting prices')

        supported_currencies = [
            'BTC',
            'BCH',
            'BLK',
            'BCN',
            'DASH',
            'DOGE',
            'EMC',
            'ETH',
            'LTC',
            'XMR',
            'PPC',
            'XPM',
            'RDD',
            'XRP',
            'ZEC'
        ]

        output = {}

        for coin in currencies:
            if coin.code in supported_currencies:
                r = requests.get(
                    url='https://api.cryptonator.com/api/ticker/{}-usd'.format(
                        coin.code.lower()
                    )
                )

                if r.status_code != requests.codes.ok:
                    return None, 'bad status code: {}'.format(r.status_code)

                try:
                    data = r.json()
                except ValueError:
                    return None, 'no json: {}'.format(r.text)

                ticker = data.get('ticker')

                if not ticker:
                    return None, 'no ticker in data: {}'.format(data)

                output[coin] = Decimal(ticker.get('price'))

        return output, 'success'




