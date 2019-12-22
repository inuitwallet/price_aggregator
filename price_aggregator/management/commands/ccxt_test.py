import logging
import math
from datetime import timedelta
from decimal import Decimal

import ccxt
from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator.models import Currency, AggregatedPrice, Provider, ProviderBlackList, ProviderResponse

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-e',
            '--exchange',
            help='The exchange',
            dest='exchange'
        )

    @staticmethod
    def get_latest_agg_price(currency):
        if currency.upper() == 'USD':
            return 1

        current_agg_price = AggregatedPrice.objects.filter(
            currency__code=currency.upper()
        ).first()

        if current_agg_price is None:
            return None

        return current_agg_price.aggregated_price

    def handle(self, *args, **options):
        """
        Get the ticker response from a single exchange via the ccxt wrapper
        """
        exchange = options['exchange']
        logger.info('Working on {}'.format(exchange))
        try:
            wrapper = getattr(ccxt, exchange)()
        except Exception:
            logger.error('No exchange named {}'.format(exchange))
            return

        logger.info('{}: Getting Prices via CCXT'.format(exchange.title()))

        currencies = Currency.objects.all()
        currency_check_list = [c.code.upper() for c in currencies] + ['USD']

        try:
            markets = wrapper.fetch_markets()
        except Exception as e:
            logger.error('Failed to fetch markets')
            return

        prices = []

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

            # get the volumes
            if ticker['baseVolume'] is not None:
                base_volume = Decimal(ticker['baseVolume'])
            else:
                base_volume = Decimal(0.0)

            if ticker['quoteVolume'] is not None:
                quote_volume = Decimal(ticker['quoteVolume'])
            else:
                quote_volume = Decimal(0.0)

            current_base_price_usd = self.get_latest_agg_price(market['base'])
            current_quote_price_usd = self.get_latest_agg_price(market['quote'])

            last_base_price_usd = Decimal(current_quote_price_usd * last_price)
            base_volume_usd = Decimal(base_volume * current_base_price_usd)

            last_quote_price_usd = Decimal(current_base_price_usd / last_price)
            quote_volume_usd = Decimal(quote_volume * current_quote_price_usd)

            for coin in currencies:
                if coin.code.upper() == market['base'].upper():
                    prices.append(
                        {
                            'coin': coin,
                            'price': last_base_price_usd,
                            'market_price': last_price,
                            'provider': '{}_{}_{}_market'.format(exchange.title(), market['base'], market['quote']),
                            'volume': base_volume_usd
                        }
                    )
                if coin.code.upper() == market['quote'].upper():
                    prices.append(
                        {
                            'coin': coin,
                            'price': last_quote_price_usd,
                            'market_price': 1 / last_price,
                            'provider': '{}_{}_{}_market'.format(exchange.title(), market['base'], market['quote']),
                            'volume': quote_volume_usd
                        }
                    )

        for price in prices:
            try:
                price_provider = Provider.objects.get(name__iexact=price['provider'])
            except Provider.DoesNotExist:
                # the market_provider field comes from the 'parent' provider
                price_provider = Provider.objects.create(
                    name=price['provider'],
                    exchange_provider=True,
                    cache=300
                )

            # if the provider is blacklisted, we skip.
            # We perform this check here otherwise market_providers cannot be individually blacklisted
            try:
                ProviderBlackList.objects.get(currency=price['coin'], provider=price_provider)
                continue
            except ProviderBlackList.DoesNotExist:
                pass

            if math.isnan(price['price']):
                continue

            logger.info('Saving {} from {}: {:.8f}'.format(price['coin'], price_provider.name, price['price']))

            ProviderResponse.objects.create(
                provider=price_provider,
                currency=price['coin'],
                value=price['price'],
                market_value=price.get('market_price', 0),
                volume=price.get('volume'),
                update_by=now() + timedelta(seconds=price_provider.cache)
            )
