import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenExchangeRates(object):
    """
    https://www.bitstamp.net/api/eur_usd/
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('OpenExchangeRates: Getting prices')

        r = requests.get(
            url='https://openexchangerates.org/api/latest.json?app_id={}'.format(
                settings.OPENEXCHANGERATES_APP_ID
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
            return None, 'no rates found in data: {}'.format(data)

        search_codes = [coin.code.upper() for coin in currencies]
        output = {}

        for currency in rates:
            if currency in search_codes:
                for coin in currencies:
                    if coin.code.upper() == currency:
                        output[coin] = Decimal(1 / rates.get(currency))

        return output, 'success'
