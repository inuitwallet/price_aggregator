import logging
import time
from datetime import timedelta

from django.core.management import BaseCommand
from django.core.paginator import Paginator
from django.utils.timezone import now

from price_aggregator.models import ProviderResponse, AggregatedPrice

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--days',
            help='how many days ago to delete responses before',
            dest='days',
            default=30
        )

    def handle(self, *args, **options):
        responses = ProviderResponse.objects.filter(
            date_time__lte=now() - timedelta(days=int(options['days']))
        ).order_by('date_time')

        logger.info(f'Deleting {responses.count()} responses')
        time.sleep(2)

        for response in responses:
            logger.info(f'Deleting {response}')
            logger.info(response.delete())

