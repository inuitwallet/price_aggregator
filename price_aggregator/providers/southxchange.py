import logging
from decimal import Decimal

import requests
from django.conf import settings

from price_aggregator.models import AggregatedPrice

logger = logging.getLogger(__name__)


class SouthXchange(object):
    """
    https://www.southxchange.com/Home/Api#prices
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('SouthXchange: Getting prices')

        # get the market summaries
        r = requests.get(
            url='https://www.southxchange.com/api/prices'
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
            market = market_data.get('Market')
            base_coin = market.split('/')[0]
            market_coin = market.split('/')[1]

            if not market_coin:
                continue

            if market_coin not in ['USNBT', 'NSR']:
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
                            current_prices[base_coin] = None
                            continue

                        current_prices[base_coin] = current_agg_price.aggregated_price

                    # get the price from the current_prices dict
                    current_price = current_prices.get(base_coin)

                    if current_price is None:
                        # skip this one as we don't have a USD calculation
                        continue

                for coin in currencies:
                    if coin.code.upper() == market_coin:
                        price = market_data.get('Last', 0.0)

                        if price is None:
                            price = 0.0

                        if price > 0.0:
                            price = Decimal(1 / price)

                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(price * current_price),
                                'market_price': price,
                                'provider': 'SouthXchange_{}_market'.format(base_coin)
                            }
                        )

        return output, 'success'


