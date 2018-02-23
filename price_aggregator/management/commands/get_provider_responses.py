import logging
from datetime import timedelta

from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator import providers
from price_aggregator.models import Currency, ProviderFailure, ProviderResponse, Provider

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--provider',
            help='The provider to get a response from',
            dest='provider'
        )

    def handle(self, *args, **options):
        if options['provider']:
            providers_names = [options['provider']]
        else:
            providers_names = providers.__all__

        currencies = Currency.objects.all()

        for provider_name in providers_names:
            try:
                provider = Provider.objects.get(name=provider_name)
            except Provider.DoesNotExist:
                logger.error('No provider named {}'.format(provider_name))
                continue

            logger.info('Working on provider {}'.format(provider_name))

            # see if the cache time has lapsed
            last_response = ProviderResponse.objects.filter(
                provider=provider
            ).order_by(
                '-date_time'
            ).first()

            if last_response:
                cache_time = last_response.date_time + timedelta(seconds=provider.cache)

                # use the timedelta to check if the cache is about to expire.
                # Without this we get gaps in provider data.
                # With it we get some overlap although cache times may need to be tweaked
                if (now() + timedelta(minutes=2)) < cache_time:
                    logger.warning(
                        'Cache time not yet elapsed for {}. Wait until {}'.format(
                            provider,
                            cache_time
                        )
                    )
                    continue

            provider_wrapper = getattr(providers, provider_name)
            prices, message = provider_wrapper.get_prices(currencies=currencies)

            if prices is None:
                logger.error('{} failure: {}'.format(provider, message))
                ProviderFailure.objects.create(
                    provider=provider,
                    message=message
                )
                continue

            # we have some price data
            for currency in prices:
                logger.info('Saving {} from {}'.format(currency, provider_name))
                ProviderResponse.objects.create(
                    provider=provider,
                    currency=currency,
                    value=prices.get(currency),
                    update_by=now() + timedelta(seconds=provider.cache)
                )
