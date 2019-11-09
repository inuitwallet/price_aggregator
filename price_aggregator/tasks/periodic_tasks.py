from celery import signature, group

from price_aggregator import providers
from price_aggregator.celery import app
from price_aggregator import tasks
from celery.utils.log import get_task_logger

from price_aggregator.models import Currency

logger = get_task_logger(__name__)


@app.task
def get_provider_responses():
    """
    Get the price responses from the various providers
    """
    providers_names = providers.__all__
    provider_list = []

    for provider_name in providers_names:
        # generate a task signature for this provider
        provider_sig = signature(
            getattr(tasks, 'get_provider_response'),
            kwargs={
                'provider_name': provider_name
            },
            immutable=True
        )
        # append to the list of signatures
        provider_list.append(provider_sig)

    # turn the list of signatures into a Celery group
    provider_group = group(provider_list)
    # then run the group
    provider_group.apply_async()


@app.task
def calculate_aggregates():
    """
    Calculate the aggregate prices from the latest provider responses
    """
    aggregate_list = []

    for currency in Currency.objects.all():
        # build the signature for this aggregation
        aggregate_sig = signature(
            getattr(tasks, 'calculate_aggregate'),
            kwargs={
                'currency_pk': currency.pk
            },
            immutable=True
        )
        # append to the list of signatures
        aggregate_list.append(aggregate_sig)

    # turn the list of signatures into a Celery group
    aggregate_group = group(aggregate_list)
    # then run the group
    aggregate_group.apply_async()


