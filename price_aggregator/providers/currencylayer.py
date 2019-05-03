import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class CurrencyLayer(object):
    """
    https://currencylayer.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CurrencyLayer: Getting prices')

        r = requests.get(
            url='http://apilayer.net/api/live?access_key={}&format=1'.format(
                settings.CURRENCYLAYER_API_KEY
            )
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        quotes = data.get('quotes')

        if not quotes:
            return None, 'no quotes in data: {]'.format(data)

        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        for pair in quotes:
            currency_code = pair.replace('USD', '')
            if currency_code in search_codes:
                for coin in currencies:
                    if coin.code.upper() == currency_code:
                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(1 / quotes.get(pair))
                            }
                        )

        return output, 'success'


