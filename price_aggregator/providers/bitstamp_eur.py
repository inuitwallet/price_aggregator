import logging
from decimal import Decimal

import requests


logger = logging.getLogger(__name__)


class BitStampEur(object):
    """
    https://www.bitstamp.net/api/eur_usd/
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('BitStampEur: Getting prices')

        EUR = None

        for currency in currencies:
            if currency.code.upper() == 'EUR':
                EUR = currency

        if not EUR:
            return {}, 'no eur in listed currencies'

        r = requests.get(
            url='https://www.bitstamp.net/api/eur_usd/'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        buy = data.get('buy')

        if not buy:
            return None, 'no buy price found: {}'.format(data)

        sell = data.get('sell')

        if not sell:
            return None, 'no sell price found: {}'.format(data)

        return [{'coin': EUR, 'price': Decimal((Decimal(buy) + Decimal(sell)) / 2)}], 'success'
