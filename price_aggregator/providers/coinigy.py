import json
import logging
from decimal import Decimal
from statistics import mean

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class Coinigy(object):
    """
    https://coinigy.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Coinigy: Getting prices')

        r = requests.post(
            url='https://api.coinigy.com/api/v1/markets',
            headers={
                'Content-Type': 'application/json',
                'X-API-KEY': settings.COINIGY_API_KEY,
                'X-API-SECRET': settings.COINIGY_API_SECRET
            }
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code getting markets: {}'.format(r.status_code)

        try:
            markets_data = r.json()
        except ValueError:
            return None, 'no json getting markets: {}'.format(r.text)

        markets = markets_data.get('data')

        if not markets:
            return None, 'no data in marekt_data: {}'.format(markets_data)

        search_codes = [coin.code.upper() for coin in currencies]
        prices = {}

        for market in markets:
            pair = market.get('mkt_name').split('/')

            if len(pair) < 2:
                continue

            if pair[1] != 'USD':
                continue

            if pair[0] in search_codes:
                r = requests.post(
                    url='https://api.coinigy.com/api/v1/ticker',
                    data=json.dumps(
                        {
                            'exchange_code': market.get('exch_code'),
                            'exchange_market': market.get('mkt_name')
                        }
                    ),
                    headers={
                        'Content-Type': 'application/json',
                        'X-API-KEY': settings.COINIGY_API_KEY,
                        'X-API-SECRET': settings.COINIGY_API_SECRET
                    }
                )

                if r.status_code != requests.codes.ok:
                    logger.warning(
                        'bad status code getting {}@{}: {}'.format(
                            pair[0],
                            market.get('exch_code'),
                            r.status_code
                        )
                    )
                    continue

                try:
                    ticker_data = r.json()
                except ValueError:
                    logger.warning(
                        'no json getting {}@{}: {}'.format(
                            pair[0],
                            market.get('exch_code'),
                            r.text
                        )
                    )
                    continue

                ticker = ticker_data.get('data')

                if not ticker:
                    logger.warning(
                        'no data found in ticker for {}@{}: {}'.format(
                            pair[0],
                            market.get('exch_code'),
                            ticker_data
                        )
                    )
                    continue

                if pair[0] not in prices:
                    prices[pair[0]] = []

                prices[pair[0]].append(float(ticker[0].get('last_trade')))

        output = {}

        for prices_coin in prices:
            for coin in currencies:
                if coin.code.upper() == prices_coin:
                    output[coin] = Decimal(mean(prices[prices_coin]))

        return output, 'success'
