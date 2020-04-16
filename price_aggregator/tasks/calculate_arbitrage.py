import itertools
from datetime import timedelta

from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from django.utils.timezone import now

from price_aggregator.celery import app
from price_aggregator.models import Currency, ProviderResponse, ArbitrageOpportunity

logger = get_task_logger(__name__)


@app.task
def calculate_arbitrage(currency_pk):
    """
    Calculate the aggregate price for the given currency
    """
    currency = Currency.objects.get(pk=currency_pk)
    logger.info('Working on {}'.format(currency))

    # get the distinct providers from the provider responses
    # this query ensures we get only the latest price from each provider
    # db_responses = ProviderResponse.objects.filter(
    #     currency=currency,
    #     update_by__gte=now(),
    #     provider__exchange_provider=True,
    #     provider__active=True
    # )

    db_responses = ProviderResponse.objects.filter(
        currency=currency,
        provider__exchange_provider=True,
        provider__active=True
    )[:3]

    if db_responses.count() == 0:
        logger.warning('Got no valid responses for {}'.format(currency))
        raise Ignore()

    for combination in itertools.combinations(db_responses, 2):
        if combination[0].value > combination[1].value:
            high_provider_response = combination[0]
            low_provider_response = combination[1]
        else:
            high_provider_response = combination[1]
            low_provider_response = combination[0]

        difference = high_provider_response.value - low_provider_response.value
        average = (high_provider_response.value + low_provider_response.value) / 2
        percentage_difference = (difference / average) * 100

        if percentage_difference > 10:
            logger.warning(
                f'{currency} Found % diff of {percentage_difference} between '
                f'{combination[0].provider} and {combination[1].provider}'
                f'({combination[0].value} - {combination[1].value}'
            )
            ArbitrageOpportunity.objects.create(
                currency=currency,
                low_provider_response=low_provider_response,
                high_provider_response=high_provider_response
            )
