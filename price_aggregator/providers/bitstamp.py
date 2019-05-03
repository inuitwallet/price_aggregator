import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


class BitStamp(object):
    """
    https://www.bitstamp.net
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Bitstamp: Getting prices')

        supported_currencies = ['BTC', 'EUR', 'XRP', 'LTC', 'ETH', 'BCH']
        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        for currency_code in set(search_codes).intersection(supported_currencies):
            r = requests.get(
                url='https://www.bitstamp.net/api/v2/ticker/{}usd'.format(
                    currency_code.lower()
                )
            )

            if r.status_code != requests.codes.ok:
                return None, 'bad status code getting {}: {}'.format(
                    currency_code,
                    r.status_code
                )

            try:
                data = r.json()
            except ValueError:
                return None, 'no json getting {}: {}'.format(currency_code, r.text)

            for coin in currencies:
                if coin.code.upper() == currency_code.upper():
                    output.append(
                        {
                            'coin': coin,
                            'price': Decimal(data.get('last'))
                        }
                    )

        return output, 'success'


