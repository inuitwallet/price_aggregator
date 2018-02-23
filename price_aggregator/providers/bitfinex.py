import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


class Bitfinex(object):
    """
    https://www.bitfinex.com/
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Bitfinex: Getting prices')

        # get the symbols
        r = requests.get(
            url='https://api.bitfinex.com/v1/symbols'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code getting symbols: {}'.format(r.status_code)

        try:
            symbols = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        search_codes = [coin.code.upper() for coin in currencies]
        output = {}

        for symbol in symbols:
            if 'usd' not in symbol:
                continue

            cleaned_symbol = symbol.replace('usd', '')

            if cleaned_symbol.upper() in search_codes:
                r = requests.get(
                    url='https://api.bitfinex.com/v1/pubticker/{}'.format(symbol)
                )
                if r.status_code != requests.codes.ok:
                    return None, 'bad status code getting {}: {}'.format(
                        symbol,
                        r.status_code
                    )

                try:
                    data = r.json()
                except ValueError:
                    return None, 'no json getting {}: {}'.format(symbol, r.text)

                for coin in currencies:
                    if coin.code.upper() == cleaned_symbol.upper():
                        output[coin] = Decimal(data.get('mid'))

        return output, 'success'
