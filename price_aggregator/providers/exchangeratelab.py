import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ExchangeRateLab(object):
    """
    http://www.exchangeratelab.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CryptoCompare: Getting prices')

        r = requests.get(
            url='http://api.exchangeratelab.com/api/current/USD?apikey={}'.format(
                settings.EXCHANGERATELAB_API_KEY
            )
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        rates = data.get('rates')

        if not rates:
            return None, 'no rates in data: {}'.format(data)

        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        for currency in rates:
            if currency.get('to') in search_codes:
                for coin in currencies:
                    if coin.code.upper() == currency.get('to'):
                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(1 / currency.get('rate'))
                            }
                        )

        return output, 'success'
