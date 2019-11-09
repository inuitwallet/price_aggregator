import logging
from datetime import timedelta

from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator import providers
from price_aggregator.models import Currency, ProviderFailure, ProviderResponse, Provider, ProviderBlackList

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--provider',
            help='The provider to get a response from',
            dest='provider'
        )
        parser.add_argument(
            '-f',
            '--force',
            help='Request even if cache hasn\'t expired',
            action='store_true'
        )
        parser.add_argument(
            '-s',
            '--skip-save',
            help='Don\'t save the collected data',
            action='store_true'
        )

    def handle(self, *args, **options):
        if options['provider']:
            providers_names = [options['provider']]
        else:
            providers_names = providers.__all__

        currencies = Currency.objects.all()

        for provider_name in providers_names:
            # make sure the named provider has been created
            # (the add_providers management command can be run to add newly created ones)
            try:
                provider = Provider.objects.get(name__iexact=provider_name)
            except Provider.DoesNotExist:
                logger.error('No provider named {}'.format(provider_name))
                continue

            if not provider.active:
                logger.warning('{} is not active. Skipping!'.format(provider_name))
                continue

            logger.info('Working on provider {}'.format(provider.name))

            # see if the cache time has lapsed
            last_response = ProviderResponse.objects.filter(
                provider=provider
            ).first()

            if last_response and not options['force']:
                cache_time = last_response.date_time + timedelta(seconds=provider.cache)

                # use the timedelta to check if the cache is about to expire.
                # Without this we get gaps in provider data.
                # With it we get some overlap although cache times may need to be tweaked
                cache_time = cache_time - timedelta(minutes=1)

                if now() < cache_time:
                    logger.warning(
                        'Cache not yet expired for {}. Wait until {}'.format(
                            provider,
                            cache_time
                        )
                    )
                    continue

            # get the provider code and get the prices
            provider_wrapper = getattr(providers, provider.name)
            prices, message = provider_wrapper.get_prices(currencies=currencies)

            if prices is None:
                # getting the prices failed. Log the error and move on
                logger.error('{} failure: {}'.format(provider, message))
                ProviderFailure.objects.create(
                    provider=provider,
                    message=message
                )
                continue

            # we have some price data
            for price in prices:
                # new providers can be created from new market data as 'market_providers'
                # the name of the market_provider is passed back in the price data under the 'provider' key
                try:
                    price_provider = Provider.objects.get(name__iexact=price.get('provider', provider_name))
                except Provider.DoesNotExist:
                    # the market_provider field comes from the 'parent' provider
                    price_provider = Provider.objects.create(
                        name=price.get('provider', provider_name),
                        market_provider=provider.market_provider,
                        cache=provider.cache
                    )

                # if the provider is blacklisted, we skip.
                # We perform this check here otherwise market_providers cannot be individually blacklisted
                try:
                    ProviderBlackList.objects.get(currency=price['coin'], provider=price_provider)
                    continue
                except ProviderBlackList.DoesNotExist:
                    pass

                if options['skip_save']:
                    logger.info(
                        'Skipping save of {} from {}: {:.8f}'.format(price['coin'], price_provider.name, price['price'])
                    )
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
