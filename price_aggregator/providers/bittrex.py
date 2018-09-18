import logging
from decimal import Decimal

import requests
from django.conf import settings

from price_aggregator.models import AggregatedPrice

logger = logging.getLogger(__name__)


class Bittrex(object):
    """
    https://www.coinapi.io
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Bittrex: Getting prices')

        # get the market summaries

        r = requests.get(
            url='https://bittrex.com/api/v1.1/public/getmarketsummaries',
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        results = data.get('result')

        if not results:
            return None, 'no quotes in data: {]'.format(data)

        search_codes = [coin.code.upper() for coin in currencies]
        output = {}

        current_prices = {}

        for market_data in results:
            base_coin = market_data.get('MarketName', '-').split('-')[0]
            market_coin = market_data.get('MarketName', '-').split('-')[1]

            # Bittrex still call USNubits NBT
            if market_coin == 'NBT':
                market_coin = 'USNBT'

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
                        # skip this one as we don;t have a USD calculation
                        continue

                for coin in currencies:
                    if coin.code.upper() == market_coin:
                        output[coin] = Decimal(Decimal(market_data.get('Last', 0)) * current_price)

        return output, 'success'


