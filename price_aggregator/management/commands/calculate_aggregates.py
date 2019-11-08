import datetime
import logging
import os
from decimal import Decimal

import numpy as np
from django.core.management import BaseCommand
from django.utils.timezone import now

from price_aggregator.models import Currency, AggregatedPrice, ProviderResponse, Provider

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    @staticmethod
    def remove_outliers(responses):
        ys = [float(resp.value) for resp in responses]

        if not ys:
            return responses

        quartile_1, quartile_3 = np.percentile(ys, [25, 75])
        iqr = quartile_3 - quartile_1
        lower_bound = quartile_1 - (iqr * 1.5)
        upper_bound = quartile_3 + (iqr * 1.5)

        cleaned_values = []

        for response in responses:
            if float(response.value) > float(upper_bound):
                continue

            if float(response.value) < float(lower_bound):
                continue

            cleaned_values.append(response)

        return cleaned_values

    def calculate_weighted_mean(self, currency, responses):
        # some responses come from exchange pairs so should be weighted by volume
        valid_responses = []
        weighted_responses = []
        used_providers = []

        for response in responses:
            if response.volume is None:
                # we can assume that there is no volume hence this isn't an exchange response
                valid_responses.append(response)
                continue

            if response.provider in used_providers:
                continue

            used_providers.append(response.provider)
            weighted_responses.append(response)

        if len(weighted_responses) > 0 and sum([float(resp.volume) for resp in weighted_responses]) > 0.0:
            # we now have a list of values and their corresponding volumes.
            # remove outliers
            cleaned_weighted_reponses = self.remove_outliers(weighted_responses)
            # find the weighted mean
            weighted_mean = np.average(
                [float(resp.value) for resp in cleaned_weighted_reponses],
                weights=[float(resp.volume) for resp in cleaned_weighted_reponses]
            )
            # the next step expects a list of response objects so we make one now
            try:
                weighted_provider = Provider.objects.get(name__iexact='Exchange Pairs Volume Weighted Average')
            except Provider.DoesNotExist:
                weighted_provider = Provider.objects.create(name='Exchange Pairs Volume Weighted Average')

            calc_response = ProviderResponse.objects.create(
                provider=weighted_provider,
                value=weighted_mean,
                currency=currency,
                update_by=now()
            )

            # add the responses that were used here
            for response in weighted_responses:
                response.parent_response = calc_response
                response.save()

            valid_responses.append(calc_response)

        return valid_responses

    def handle(self, *args, **options):
        # check for lock file
        if os.path.exists('aggregates.lock'):
            last_aggregated_price = AggregatedPrice.objects.all().first()

            if last_aggregated_price.date_time < now() - datetime.timedelta(minutes=10):
                print('No aggregated prices for 10 minutes. Ignoring lock')
            else:
                print('Already running')
                return

        # if we got here we should lock
        open('aggregates.lock', 'w+').close()

        for currency in Currency.objects.all():
            logger.info('Working on {}'.format(currency))

            # get the distinct providers from the provider responses
            # this query ensures we get only the latest price from each provider
            db_responses = ProviderResponse.objects.filter(
                currency=currency,
                update_by__gte=now(),
                provider__active=True
            )
            # ).order_by(
            #     'provider',
            #     '-date_time'
            # ).distinct(
            #     'provider'
            # )

            if db_responses.count() == 0:
                logger.warning('Got no valid responses for {}'.format(currency))
                continue

            # get valid responses
            # this includes calculating a weighted mean of any volume bound values
            valid_responses = self.calculate_weighted_mean(currency, db_responses)

            # now we can remove outliers
            cleaned_responses = self.remove_outliers(valid_responses)

            # we just want the values in order to use the numpy functions below
            cleaned_values = [float(resp.value) for resp in cleaned_responses if resp.value > Decimal(0)]

            logger.info(
                'Got aggregated price of {} for {}'.format(np.mean(cleaned_values), currency)
            )
            aggregated_price = AggregatedPrice.objects.create(
                currency=currency,
                aggregated_price=np.mean(cleaned_values),
                providers=len(cleaned_values),
                standard_deviation=np.std(cleaned_values),
                variance=np.var(cleaned_values)
            )

            for resp in cleaned_responses:
                aggregated_price.used_responses.add(resp)

        # we're done. remove the lock
        os.remove('aggregates.lock')
