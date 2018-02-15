import logging
from decimal import Decimal

import requests


logger = logging.getLogger(__name__)


class CoinMarketCap(object):
    """
    https://coinmarketcap.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CoinMarketCap: Getting prices')

        r = requests.get(
            url='https://api.coinmarketcap.com/v1/ticker/?limit=0'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        search_codes = [coin.code.upper() for coin in currencies]
        output = {}

        for coin_data in data:
            if coin_data.get('symbol') in search_codes:
                for coin in currencies:
                    if coin.code.upper() == coin_data.get('symbol'):
                        output[coin] = Decimal(coin_data.get('price_usd'))

        return output, 'success'
