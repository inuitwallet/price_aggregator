import logging

from django.core.management import BaseCommand

from price_aggregator import providers
from price_aggregator.models import Provider

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for provider in providers.__all__:
            prov, created = Provider.objects.get_or_create(
                name=provider
            )
            if created:
                logger.info('created new provider {}'.format(provider))
            else:
                logger.info('skipping already existing provider {}'.format(provider))
