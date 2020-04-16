from django.core.management import BaseCommand

from price_aggregator.models import Currency


class Command(BaseCommand):
    def handle(self, *args, **options):
        currency = Currency.objects.get(pk=currency_pk)
        logger.info('Working on {}'.format(currency))

        # get the distinct providers from the provider responses
        # this query ensures we get only the latest price from each provider
        db_responses = ProviderResponse.objects.filter(
            currency=currency,
            update_by__gte=now(),
            provider__exchange_provider=True,
            provider__active=True
        )

        if db_responses.count() == 0:
            logger.warning('Got no valid responses for {}'.format(currency))
            raise Ignore()

        print(itertools.combinations(db_responses, 2))