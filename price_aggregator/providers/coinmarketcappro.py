import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class CoinMarketCapPro(object):
    """
    https://coinmarketcap.com/api/documentation/v1/
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CoinMarketCapPro: Getting prices')

        r = requests.get(
            url='https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
            params={
                'symbol': 'ARK,BCH,BTC,DASH,DOGE,ETH,GCN,LTC,NSR,PNX,PPC,RVN,USDT,USNBT,XMR,XQR,XRP,ZEC'
            },
            headers={
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': settings.CMC_PRO_API_KEY,
            }
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        status = data.get('status', {})

        if status.get('error_code'):
            return None, status.get('error_message')

        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        coin_data = data.get('data', {})

        for coin in coin_data:
            if coin.upper() not in search_codes:
                continue

            for currency in currencies:
                if currency.code.upper() == coin.upper():
                    output.append(
                        {
                            'coin': currency,
                            'price': Decimal(coin_data[coin].get('quote', {}).get('USD', {}).get('price', 0)),
                            'volume': Decimal(coin_data[coin].get('quote', {}).get('USD', {}).get('volume_24h', 0))
                        }
                    )

        return output, 'success'
