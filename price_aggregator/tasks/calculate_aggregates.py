from decimal import Decimal

import numpy as np

from celery.exceptions import Ignore
from django.utils.timezone import now

from price_aggregator.celery import app
from price_aggregator.models import Currency, ProviderResponse, Provider, AggregatedPrice
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@app.task
def calculate_aggregate(currency_pk):
    """
    Calculate the aggregate price for the given currency
    """
    currency = Currency.objects.get(pk=currency_pk)
    logger.info('Working on {}'.format(currency))

    # get the distinct providers from the provider responses
    # this query ensures we get only the latest price from each provider
    db_responses = ProviderResponse.objects.filter(
        currency=currency,
        update_by__gte=now(),
        provider__active=True
    )

    if db_responses.count() == 0:
        logger.warning('Got no valid responses for {}'.format(currency))
        raise Ignore()

    # get valid responses
    # this includes calculating a weighted mean of any 'market_provider' responses
    valid_responses = calculate_weighted_mean(currency, db_responses)

    # now we can remove outliers
    cleaned_responses = remove_outliers(valid_responses)

    # we want the values in order to use the numpy functions below
    cleaned_values = [float(resp.value) for resp in cleaned_responses if resp.value > Decimal(0)]

    logger.info(
        'Got an aggregated price of {} for {}'.format(np.mean(cleaned_values), currency)
    )

    # create the aggregated price object
    aggregated_price = AggregatedPrice.objects.create(
        currency=currency,
        aggregated_price=np.mean(cleaned_values),
        providers=len(cleaned_values),
        standard_deviation=np.std(cleaned_values),
        variance=np.var(cleaned_values)
    )

    # then add the cleaned responses so the api shows which responses were used
    for resp in cleaned_responses:
        aggregated_price.used_responses.add(resp)


def calculate_weighted_mean(currency, responses):
    """
    some responses come from exchange pairs so should be weighted by volume
    """
    valid_responses = []
    weighted_responses = []
    used_providers = []

    for response in responses:
        if response.provider in used_providers:
            continue

        used_providers.append(response.provider)

        if response.provider.exchange_provider:
            # this is a market_provider so should be weighted
            weighted_responses.append(response)
        else:
            # this is a standard response so should be treated as valid of itself
            valid_responses.append(response)

    if len(weighted_responses) > 0 and sum([float(resp.volume) for resp in weighted_responses]) > 0.0:
        # we now have a list of values and their corresponding volumes.
        # remove outliers
        cleaned_weighted_responses = remove_outliers(weighted_responses)
        # find the weighted mean
        weighted_mean = np.average(
            [float(resp.value) for resp in cleaned_weighted_responses],
            weights=[float(resp.volume) for resp in cleaned_weighted_responses]
        )

        # the next step expects a list of response objects so we make one now
        # first we assign a special Provider to the result
        try:
            weighted_provider = Provider.objects.get(name__iexact='Exchange Pairs Volume Weighted Average')
        except Provider.DoesNotExist:
            weighted_provider = Provider.objects.create(name='Exchange Pairs Volume Weighted Average')

        # now we generate the response object
        calc_response = ProviderResponse.objects.create(
            provider=weighted_provider,
            value=weighted_mean,
            currency=currency,
            update_by=now()
        )

        # for weighted responses we add the calculated_response from above as the 'parent_response'
        # to allow tracking of where the values came from
        for response in weighted_responses:
            response.parent_response = calc_response
            response.save()

        valid_responses.append(calc_response)

    return valid_responses


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
