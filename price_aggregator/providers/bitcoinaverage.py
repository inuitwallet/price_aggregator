import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BitcoinAverage(object):
    """
    https://bitcoinaverage.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('BitcoinAverage: Getting prices')

        r = requests.get(
            url='https://apiv2.bitcoinaverage.com/indices/global/ticker/BTCUSD',
            headers={
                'x-ba-key': settings.BITCOINAVERAGE_API_KEY
            }
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code getting symbols: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        for pair in data:
            coin_symbol = pair.replace('USD', '')

            if coin_symbol.upper() in search_codes:
                pair_data = data.get(pair)

                if not pair_data:
                    continue

                for coin in currencies:
                    if coin.code.upper() == coin_symbol.upper():
                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(pair_data.get('last'))
                            }
                        )

        return output, 'success'
