import logging
import math
from decimal import Decimal

import requests
from django.conf import settings

from price_aggregator.models import AggregatedPrice

logger = logging.getLogger(__name__)


class Altilly(object):
    """
    https://www.altilly.com/page/restapi
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Altilly: Getting prices')

        # get the market symbols
        r = requests.get(
            url='https://api.altilly.com/api/public/symbol'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            symbols = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        # get the market summaries
        r = requests.get(
            url='https://api.altilly.com/api/public/ticker'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        search_codes = [coin.code.upper() for coin in currencies]

        output = []
        current_prices = {}

        for market_data in data:
            market_symbol = market_data.get('symbol')
            market_coin = None
            base_coin = None

            for symbol in symbols:
                if symbol.get('id') == market_symbol:
                    # Altilly have their currencies inverted for some reason
                    base_coin = symbol.get('quoteCurrency')
                    market_coin = symbol.get('baseCurrency')

            if not market_coin:
                continue

            if not base_coin:
                continue

            if market_coin in search_codes:
                # if the base coin isn't USD we need to convert to USD
                current_price = 1

                if base_coin != 'USD':
                    if base_coin not in current_prices:
                        # do this bit to save the current prices to reduce database hits
                        current_agg_price = AggregatedPrice.objects.filter(
                            currency__code=base_coin
                        ).first()

                        if current_agg_price is None:
                            # save as None if not found. Saves hitting the database again and we can handle in a bit
                            current_prices[base_coin] = Decimal(0)
                            continue

                        current_prices[base_coin] = current_agg_price.aggregated_price

                    # get the price from the current_prices dict
                    current_price = current_prices.get(base_coin, Decimal(0))

                if current_price is None:
                    # skip this one as we don't have a USD calculation
                    continue

                if math.isnan(current_price):
                    continue

                for coin in currencies:
                    if coin.code.upper() == market_coin:
                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(Decimal(market_data.get('last', 0.0)) * current_price),
                                'market_price': Decimal(market_data.get('last', 0.0)),
                                'provider': 'Altilly_{}_market'.format(base_coin),
                                'volume': Decimal(market_data.get('volume', 0.0))
                            }
                        )

        return output, 'success'


