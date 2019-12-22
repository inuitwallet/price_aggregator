import logging
import math
from decimal import Decimal

import requests
from price_aggregator.models import AggregatedPrice

logger = logging.getLogger(__name__)


class SouthXchange(object):
    """
    https://www.southxchange.com/Home/Api#prices
    """
    current_prices = {}

    def get_coin_current_price(self, coin):
        if coin not in self.current_prices:
            current_agg_price = AggregatedPrice.objects.filter(
                currency__code=coin
            ).first()

            if current_agg_price is None:
                # save as None if not found. Saves hitting the database again and we can handle elsewhere
                self.current_prices[coin] = None
                return

            self.current_prices[coin] = current_agg_price.aggregated_price

    def get_prices(self, currencies):
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

        for market_data in data:
            market = market_data.get('Market')
            base_coin = market.split('/')[0].upper()
            market_coin = market.split('/')[1].upper()

            if not market_coin:
                continue

            if not base_coin:
                continue

            if base_coin in search_codes:
                # price is in 'market_coin'
                # if 'market_coin isn't USD we need to convert to USD
                current_price = 1

                if market_coin != 'USD':
                    # get the current price
                    self.get_coin_current_price(market_coin)

                    # get the price from the current_prices dict
                    current_price = self.current_prices.get(market_coin)

                if current_price is None:
                    # skip this one as we don't have a USD calculation
                    continue

                if math.isnan(current_price):
                    continue

                for coin in currencies:
                    if coin.code.upper() == base_coin:
                        price = Decimal(market_data.get('Last', 0.0))

                        if price is None:
                            price = Decimal(0.0)

                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(price * current_price),
                                'market_price': price,
                                'provider': 'SouthXchange_{}_{}_market'.format(base_coin, market_coin),
                                'volume': Decimal(Decimal(market_data.get('Volume24Hr', 0.0)) * current_price)
                            }
                        )

            if market_coin in search_codes:
                # if the base coin isn't USD we need to convert to USD
                current_price = 1

                if base_coin != 'USD':
                    # get the current price
                    self.get_coin_current_price(base_coin)

                    # get the price from the current_prices dict
                    current_price = self.current_prices.get(base_coin)

                if current_price is None:
                    # skip this one as we don't have a USD calculation
                    continue

                if math.isnan(current_price):
                    continue

                for coin in currencies:
                    if coin.code.upper() == market_coin:
                        price = Decimal(market_data.get('Last', 0.0))

                        if price is None:
                            price = Decimal(0.0)

                        if price > 0.0:
                            price = Decimal(1.0 / float(price))

                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(price * current_price),
                                'market_price': price,
                                'provider': 'SouthXchange_{}_{}_market'.format(base_coin, market_coin),
                                'volume': Decimal(Decimal(market_data.get('Volume24Hr', 0.0)) * current_price)
                            }
                        )

        return output, 'success'


