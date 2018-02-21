import datetime
from statistics import mean

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from django.views import View

from price_aggregator.models import Currency, AggregatedPrice, Provider, ProviderResponse


class PriceView(View):
    @staticmethod
    def get(request, currency_code):
        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)
        # get the last aggregated price
        agg_prices = AggregatedPrice.objects.filter(
            currency=currency
        ).filter(
            date_time__gt=make_aware(
                datetime.datetime.now() - datetime.timedelta(hours=24)
            )
        ).order_by(
            '-date_time'
        )

        if not agg_prices:
            return JsonResponse(
                {'error': 'no aggregated prices found for the last 24 hours'}
            )

        agg_price = agg_prices.first().serialize()

        # calculate the moving averages
        agg_price['moving_averages'] = {
            '24_hour': 1440,
            '12_hour': 720,
            '6_hour': 360,
            '1_hour': 60,
            '30_minute': 30
        }

        for period in agg_price['moving_averages'].copy():
            agg_list = agg_prices.filter(
                date_time__gte=make_aware(
                    datetime.datetime.now() - datetime.timedelta(
                        minutes=agg_price['moving_averages'][period]
                    )
                )
            ).values_list('aggregated_price', flat=True)

            if len(agg_list) > 1:
                agg_price['moving_averages'][period] = float(
                    '{:.8f}'.format(mean(agg_list))
                )
            else:
                del agg_price['moving_averages'][period]

        return JsonResponse(agg_price)


class CurrenciesView(View):
    @staticmethod
    def get(request):
        response = {}
        currencies = Currency.objects.all()

        for currency in currencies:
            supported_providers = ProviderResponse.objects.filter(
                currency=currency
            ).distinct(
                'provider'
            ).values_list(
                'provider__name',
                flat=True
            )
            response[currency.code] = list(supported_providers)

        return JsonResponse(response)


class ProvidersView(View):
    @staticmethod
    def get(request):
        response = {}
        providers = Provider.objects.all()

        for provider in providers:
            supported_currencies = ProviderResponse.objects.filter(
                provider=provider
            ).distinct(
                'currency'
            ).values_list(
                'currency__code',
                flat=True
            )
            response[provider.name] = list(supported_currencies)

        return JsonResponse(response)
