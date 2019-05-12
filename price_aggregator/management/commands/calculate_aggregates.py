import logging
import numpy as np
from decimal import Decimal
from statistics import mean, pstdev, pvariance

from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator.models import Currency, AggregatedPrice, ProviderResponse

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def remove_outliers(self, currency, valid_responses, num_stdev=1.0):
        ys = [float(resp.value) for resp in valid_responses]
        quartile_1, quartile_3 = np.percentile(ys, [25, 75])
        iqr = quartile_3 - quartile_1
        lower_bound = quartile_1 - (iqr * 1.5)
        upper_bound = quartile_3 + (iqr * 1.5)

        cleaned_values = []

        for response in valid_responses:
            if float(response.value) > float(upper_bound):
                continue

            if float(response.value) < float(lower_bound):
                continue

            cleaned_values.append(response)

        return cleaned_values

    def handle(self, *args, **options):
        for currency in Currency.objects.all():
            logger.info('Working on {}'.format(currency))

            # get the distinct providers from the provider responses
            # this query ensures we get only the latest price from each provider
            valid_responses = ProviderResponse.objects.filter(
                currency=currency,
                update_by__gte=now()
            ).order_by(
                'provider',
                '-date_time'
            ).distinct(
                'provider'
            )

            if valid_responses.count() == 0:
                logger.warning('Got no valid responses for {}'.format(currency))
                continue

            cleaned_responses = self.remove_outliers(currency, valid_responses)

            cleaned_values = np.array([float(resp.value) for resp in cleaned_responses if resp.value > 0])

            logger.info(
                'Got aggregated price of {} for {}'.format(np.mean(cleaned_values), currency)
            )
            aggregated_price = AggregatedPrice.objects.create(
                currency=currency,
                aggregated_price=np.mean(cleaned_values),
                providers=cleaned_values.size,
                standard_deviation=np.std(cleaned_values),
                variance=np.var(cleaned_values)
            )

            for resp in cleaned_responses:
                aggregated_price.used_responses.add(resp)
