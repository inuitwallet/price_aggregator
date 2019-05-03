import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class CoinApi(object):
    """
    https://www.coinapi.io
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CoinAPI: Getting prices')

        r = requests.get(
            url='https://rest.coinapi.io/v1/exchangerate/USD',
            headers={
                'X-CoinAPI-Key': settings.COINAPI_API_KEY,
                'Accept': 'application/json',
                'Accept-Encoding': 'deflate, gzip'
            }
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        rates = data.get('rates')

        if not rates:
            return None, 'no quotes in data: {]'.format(data)

        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        for currency_data in rates:
            if currency_data.get('asset_id_quote') in search_codes:
                for coin in currencies:
                    if coin.code.upper() == currency_data.get('asset_id_quote'):
                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(1 / currency_data.get('rate'))
                            }
                        )

        return output, 'success'


