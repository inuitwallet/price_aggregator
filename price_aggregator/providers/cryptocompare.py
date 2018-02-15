import logging
from decimal import Decimal

import requests


logger = logging.getLogger(__name__)


class CryptoCompare(object):
    """
    https://www.cryptocompare.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CryptoCompare: Getting prices')

        r = requests.get(
            url='https://min-api.cryptocompare.com/data/price?fsym=USD&tsyms={}'.format(
                ','.join(coin.code.upper() for coin in currencies)
            )
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        search_codes = [coin.code.upper() for coin in currencies]
        output = {}

        for currency in data:
            if currency in search_codes:
                for coin in currencies:
                    if coin.code.upper() == currency:
                        output[coin] = Decimal(1 / data.get(currency))

        return output, 'success'
