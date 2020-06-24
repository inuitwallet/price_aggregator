from datetime import timedelta

from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator.models import ProviderResponse


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--days',
            help='how many days ago to delete responses before',
            dest='days'
        )

    def handle(self, *args, **options):
        for response in ProviderResponse.objects.filter(date_time__let=now() - timedelta(days=options['days'])):
            print(f'Deleting {response}')
            response.delete()

