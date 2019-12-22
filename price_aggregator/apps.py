from django.apps import AppConfig
from .tasks import *


class PriceAggregatorConfig(AppConfig):
    name = 'price_aggregator'
