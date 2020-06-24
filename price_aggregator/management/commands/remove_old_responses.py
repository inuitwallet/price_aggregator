import logging
from datetime import timedelta

from django.core.management import BaseCommand
from django.core.paginator import Paginator
from django.utils.timezone import now

from price_aggregator.models import ProviderResponse

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--days',
            help='how many days ago to delete responses before',
            dest='days',
            default=365
        )

    def handle(self, *args, **options):
        responses = ProviderResponse.objects.filter(
            date_time__lte=now() - timedelta(days=int(options['days']))
        ).order_by('-date_time')
        p = Paginator(responses, 20)

        for page_num in p.page_range:
            for response in p.page(page_num):
                logger.info(f'Deleting {response}')


