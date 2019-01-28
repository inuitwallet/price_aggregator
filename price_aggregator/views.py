import datetime
import json
from statistics import mean

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import make_aware, now
from django.views import View

from price_aggregator.models import Currency, AggregatedPrice, Provider, ProviderResponse, ProviderFailure


class IndexView(View):
    @staticmethod
    def get(request):
        # show somme help so other end points can be found
        request_url = '{}://{}'.format(request.META.get('HTTP_X_FORWARDED_PROTO', 'http'), request.get_host())
        return JsonResponse(
            {
                '1_site_name': 'Nu Price Aggregator',
                '2_site_function': 'Collect prices of Currencies form various sources and aggregate them. '
                                   'The aim is to create a more stable price source that is not reliant on any '
                                   'single provider. Prices are displayed in USD',
                '3_endpoints': [
                    {
                        'url': '{}/currencies'.format(request_url),
                        'url_function': 'Display all currencies that have current aggregated prices'
                    },
                    {
                        'url': '{}/providers'.format(request_url),
                        'url_function': 'Display all active providers and the currencies they provide information for'
                    },
                    {
                        'url': '{}/price/<currency_code>'.format(request_url),
                        'url_function': 'Display aggregated price data for the currency specified by <currency_code>'
                    },
                    {
                        'url': '{}/price/<currency_code>/<date_time>'.format(request_url),
                        'url_function': 'Display aggregated price data for the currency specified by <currency_code> '
                                        'at the date_time given by <date_time> (yyyy-mm-ddTHH:MM:SS)'
                    },
                    {
                        'url': '{}/movement/<currency_code>'.format(request_url),
                        'url_function': 'Display the price movement over a range of times'
                    }
                ]
            },
            json_dumps_params={
                'sort_keys': True
            }
        )


class PriceView(View):
    @staticmethod
    def get(request, currency_code):
        # Bittrex still calls USNBT NBT!
        # TODO - handle multiple codes on model?
        if currency_code.lower() == 'nbt':
            currency_code = 'usnbt'

        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)
        # get the last aggregated price
        agg_price = AggregatedPrice.objects.filter(
            currency=currency,
        ).order_by(
            '-date_time'
        ).first()

        if not agg_price:
            return JsonResponse(
                {'error': 'no aggregated prices found for the last 24 hours'}
            )

        return JsonResponse(agg_price.serialize(), json_dumps_params={'sort_keys': True})


class SpotPriceView(View):
    @staticmethod
    def get(request, currency_code, date_time):
        # Bittrex still calls USNBT NBT!
        # TODO - handle multiple codes on model?
        if currency_code.lower() == 'nbt':
            currency_code = 'usnbt'

        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)
        # get the datetime
        dt = make_aware(datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S"))

        # get the aggregated price closest to date_time
        try:
            agg_price = AggregatedPrice.objects.get_closest_to(
                currency=currency,
                target=dt
            )
        except AggregatedPrice.DoesNotExist:
            return JsonResponse(
                {'error': 'no aggregated prices found'}
            )

        return JsonResponse(agg_price.serialize(), json_dumps_params={'sort_keys': True})


class CurrenciesView(View):
    @staticmethod
    def get(request):
        response = {}
        currencies = Currency.objects.all()

        for currency in currencies:
            supported_providers = ProviderResponse.objects.filter(
                currency=currency,
                date_time__gte=now() - datetime.timedelta(days=1)
            ).values_list(
                'provider__name',
                flat=True
            )

            response[currency.code] = list(set(supported_providers))

        return JsonResponse(response, json_dumps_params={'sort_keys': True})


class ProvidersView(View):
    @staticmethod
    def get(request):
        request_url = '{}://{}'.format(request.META.get('HTTP_X_FORWARDED_PROTO', 'http'), request.get_host())
        response = {}
        providers = Provider.objects.all()

        for provider in providers:
            supported_currencies = ProviderResponse.objects.filter(
                provider=provider,
                date_time__gte=now() - datetime.timedelta(days=1)
            ).values_list(
                'currency__code',
                flat=True
            )
            response[provider.name] = {
                'supported_currencies': list(set(supported_currencies)),
                'url': '{}{}'.format(
                    request_url,
                    reverse('provider', kwargs={'provider': provider.name})
                )
            }
        return JsonResponse(response, json_dumps_params={'sort_keys': True})


class ProviderResponsesView(View):
    @staticmethod
    def get(request, provider):
        provider_obj = get_object_or_404(Provider, name__iexact=provider)
        responses = ProviderResponse.objects.filter(
            provider=provider_obj,
            date_time__gte=now() - datetime.timedelta(days=1)
        )

        return JsonResponse(
            {
                provider_obj.name: {
                    resp.currency.code: {
                        'responses': [
                            {
                                'date_time': response.date_time,
                                'value': response.value
                            } for response in responses.filter(currency=resp.currency).order_by('date_time')
                        ]
                    } for resp in responses.distinct('currency').order_by('currency')
                }
            }
        )


class PriceChangesView(View):
    @staticmethod
    def get(request, currency_code):
        # Bittrex still calls USNBT NBT!
        # TODO - handle multiple codes on model?
        if currency_code.lower() == 'nbt':
            currency_code = 'usnbt'

        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)

        return JsonResponse(currency.currency_movements())
