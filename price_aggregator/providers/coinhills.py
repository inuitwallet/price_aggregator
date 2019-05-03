import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


class CoinHills(object):
    """
    hhttps://coinhills.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CoinHills: Getting prices')

        r = requests.get(
            url='https://api.coinbase.com/v2/exchange-rates'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code getting symbols: {}'.format(r.status_code)

        try:
            resp_data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        data = resp_data.get('data')

        if not data:
            return None, 'no \'data\' element returned: {}'.format(resp_data)

        rates = data.get('rates')

        if not rates:
            return None, 'no rates returned in data: {}'.format(data)

        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        for coin_symbol in rates:
            if coin_symbol.upper() in search_codes:
                for coin in currencies:
                    if coin.code.upper() == coin_symbol.upper():
                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(1) / Decimal(rates.get(coin_symbol))
                            }
                        )

        return output, 'success'
