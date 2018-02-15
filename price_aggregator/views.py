from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View

from price_aggregator.models import Currency, AggregatedPrice


class PriceView(View):
    @staticmethod
    def get(request, currency_code):
        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)
        # get the last aggregated price
        agg_price = AggregatedPrice.objects.filter(
            currency=currency
        ).order_by(
            '-date_time'
        ).first()

        return JsonResponse(agg_price.serialize())
