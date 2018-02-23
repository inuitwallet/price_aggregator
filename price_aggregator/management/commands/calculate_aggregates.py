import logging
from decimal import Decimal
from statistics import mean, pstdev, pvariance

from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator.models import Currency, AggregatedPrice, ProviderResponse

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def remove_outliers(self, valid_responses, num_stdev=1.0):
        if valid_responses.count() <= 2:
            return valid_responses

        cleaned_responses = []
        prices = [resp.value for resp in valid_responses]
        mu = mean(prices)
        stdev = pstdev(prices, mu)
        stdev_value = (Decimal(num_stdev) * stdev)

        for resp in valid_responses:
            if resp.value > (mu + stdev_value):
                continue

            if resp.value < (mu - stdev_value):
                continue

            cleaned_responses.append(resp)

        if len(cleaned_responses) < 3:
            return self.remove_outliers(valid_responses, (num_stdev + 0.1))

        return cleaned_responses

    def handle(self, *args, **options):
        for currency in Currency.objects.all():
            logger.info('Working on {}'.format(currency))

            # get the distinct providers from the provider responses
            valid_responses = ProviderResponse.objects.filter(
                currency=currency,
                update_by__gte=now()
            )

            if valid_responses.count() == 0:
                logger.warning('Got no valid responses for {}'.format(currency))
                continue

            cleaned_responses = self.remove_outliers(valid_responses)

            # calculate the mean of all prices
            prices = [resp.value for resp in cleaned_responses]
            agg_price = mean(prices)

            logger.info(
                'Got aggregated price of {} for {}'.format(agg_price, currency)
            )
            aggregated_price = AggregatedPrice.objects.create(
                currency=currency,
                aggregated_price=agg_price,
                providers=len(prices),
                standard_deviation=pstdev(prices, agg_price),
                variance=pvariance(prices, agg_price)
            )

            for resp in cleaned_responses:
                aggregated_price.used_responses.add(resp)
