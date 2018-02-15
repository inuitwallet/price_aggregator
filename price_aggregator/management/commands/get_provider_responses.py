import logging
from datetime import timedelta

from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator import providers
from price_aggregator.models import Currency, ProviderFailure, ProviderResponse, Provider

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        currencies = Currency.objects.all()

        for provider_name in providers.__all__:
            provider = Provider.objects.get(name=provider_name)

            # see if the cache time has lapsed
            last_response = ProviderResponse.objects.filter(
                provider=provider
            ).order_by(
                '-date_time'
            ).first()

            if last_response:
                cache_time = last_response.date_time + timedelta(seconds=provider.cache)

                if now() < cache_time:
                    logger.warning(
                        'Cache time not yet elapsed for {}. Wait until {}'.format(
                            provider,
                            cache_time
                        )
                    )
                    continue

            provider_wrapper = getattr(providers, provider_name)
            prices, message = provider_wrapper.get_prices(currencies)

            if prices is None:
                logger.error('{} failure'.format(provider))
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
