import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


class CoinDesk(object):
    """
    https://www.coindesk.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CoinDesk: Getting prices')

        r = requests.get(
            url='https://api.coindesk.com/v1/bpi/currentprice.json'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code getting symbols: {}'.format(r.status_code)

        try:
            resp_data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        bpi = resp_data.get('bpi')

        if not bpi:
            return None, 'no bpi section in data: {}'.format(resp_data)

        usd_data = bpi.get('USD')

        if not usd_data:
            return None, 'no USD Data: {]'.format(bpi)

        output = {}

        for currency in currencies:
            if currency.code.upper() == 'BTC':
                output[currency] = Decimal(usd_data.get('rate_float'))

        return output, 'success'
