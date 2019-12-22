import logging
import math
from decimal import Decimal

import requests
import ccxt

from price_aggregator.models import AggregatedPrice

logger = logging.getLogger(__name__)


class CCXT(object):
    """
    https://github.com/ccxt/ccxt/
    """
    current_prices = {
        'USD': 1
    }

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
        """
        CCXT provides unified wrappers for loads of Exchanges. Ww can loop through them and get the ticker for each
        """
        currency_check_list = [c.code.upper() for c in currencies] + ['USD']
        output = []

        for exchange in ccxt.exchanges:
            try:
                wrapper = getattr(ccxt, exchange)()
            except ccxt.base.errors.NotSupported:
                continue

            if not wrapper.has['fetchTicker']:
                logger.info('No ticker available for {}'.format(exchange.title()))
                continue

            logger.info('{}: Getting Prices via CCXT'.format(exchange.title()))

            try:
                markets = wrapper.fetch_markets()
            except Exception as e:
                continue

            for market in markets:
                if market['base'].upper() not in currency_check_list:
                    continue

                if market['quote'].upper() not in currency_check_list:
                    continue

                try:
                    ticker = wrapper.fetchTicker(market['symbol'])
                except Exception:
                    continue

                if ticker['last'] is None:
                    continue

                last_price = Decimal(ticker['last'])

                if ticker['baseVolume'] is not None:
                    volume = Decimal(ticker['baseVolume'])
                else:
                    volume = Decimal(0.0)

                # last price will be in 'base' currency. We should calculate the USD value
                self.get_coin_current_price(market['base'].upper())
                current_price = self.current_prices.get(market['base'])

                if current_price is None:
                    continue

                last_price_usd = Decimal(last_price * current_price)
                volume_usd = Decimal(volume * current_price)

                for coin in currencies:
                    if coin.code.upper() == market['base']:
                        output.append(
                            {
                                'coin': coin,
                                'price': last_price_usd,
                                'market_price': last_price,
                                'provider': '{}_{}_{}_market'.format(exchange.title(), market['base'], market['quote']),
                                'volume': volume_usd
                            }
                        )

        return output, 'success'


