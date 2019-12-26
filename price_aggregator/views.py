import datetime
import json
from statistics import mean

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
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
                'Nu Price Aggregator': {
                    'Description': 'Collect prices of Currencies from various sources and aggregate them. '
                    'The aim is to create a more stable price source that is not reliant on any '
                    'single provider. Prices are displayed in USD',
                    'Endpoints': [
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
                        },
                        {
                            'url': '{}/provider/<provider>'.format(request_url),
                            'url_function': 'Display historical responses from a given provider'
                        },
                        {
                            'url': '{}/provider/<provider>/price/<currency_code>'.format(request_url),
                            'url_function': 'get the latest and moving average prices from a single provider'
                        },
                        {
                            'url': '{}/provider/<provider>/price/<currency_code>/<date_time>'.format(request_url),
                            'url_function': 'Display single provider data for the currency specified by <currency_code> '
                                            'at the date_time given by <date_time> (yyyy-mm-ddTHH:MM:SS)'
                        }
                    ]
                }
            }
        )


class PriceView(View):
    @staticmethod
    def get(request, currency_code):
        if currency_code == '<currency_code>':
            # this is a link from the front page. Allow user to choose a currency code to select
            return redirect('currency_choose', path='{}|price|{}')

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

        style = 'short'

        if 'full' in request.GET:
            style = 'full'

        return JsonResponse(agg_price.serialize(style), json_dumps_params={'sort_keys': True})


class CurrencyChooseView(View):
    @staticmethod
    def get(request, path):
        response = {}
        request_url = '{}://{}'.format(request.META.get('HTTP_X_FORWARDED_PROTO', 'http'), request.get_host())

        for currency in Currency.objects.all():
            response[currency.code] = path.replace('|', '/').format(request_url, currency.code)

        return JsonResponse(response, json_dumps_params={'sort_keys': True})


class SpotPriceView(View):
    @staticmethod
    def get(request, currency_code, date_time):
        if currency_code == '<currency_code>':
            # this is a link from the front page. Allow user to choose a currency code to select
            return redirect('currency_choose', path='{}|price|{}|<date_time>')

        if date_time == '<date_time>':
            return JsonResponse(
                {'error': 'The date_time parameter needs to be passed in the format yyyy-mm-ddTHH:MM:SS'}
            )

        # Bittrex still calls USNBT NBT!
        # TODO - handle multiple codes on model?
        if currency_code.lower() == 'nbt':
            currency_code = 'usnbt'

        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)
        # get the datetime
        try:
            dt = make_aware(datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return JsonResponse(
                {'error': 'The date_time parameter needs to be passed in the format yyyy-mm-ddTHH:MM:SS'}
            )

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

        style = 'short'

        if 'full' in request.GET:
            style = 'full'

        return JsonResponse(agg_price.serialize(style), json_dumps_params={'sort_keys': True})


class CurrenciesView(View):
    @staticmethod
    def get(request):
        response = {}
        currencies = Currency.objects.all()

        for currency in currencies:
            if 'full' in request.GET:
                supported_providers = ProviderResponse.objects.filter(
                    currency=currency,
                    date_time__gte=now() - datetime.timedelta(days=1)
                ).values_list(
                    'provider__name',
                    flat=True
                )
            else:
                supported_providers = []

            response[currency.code] = list(set(supported_providers))

        return JsonResponse(response, json_dumps_params={'sort_keys': True})


class ProviderChooseView(View):
    @staticmethod
    def get(request, path):
        response = {}
        request_url = '{}://{}'.format(request.META.get('HTTP_X_FORWARDED_PROTO', 'http'), request.get_host())

        for provider in Provider.objects.all():
            response[provider.name] = path.replace('|', '/').format(request_url, provider.name)

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
        if provider == '<provider>':
            return redirect('provider_choose', path='{}|provider|{}')

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


class ProviderPriceView(View):
    @staticmethod
    def get(request, provider, currency_code):
        if provider == '<provider>':
            return redirect(
                'provider_choose',
                path='{{}}|provider|{{}}|price|{currency_code}'.format(currency_code=currency_code)
            )

        provider_obj = get_object_or_404(Provider, name__iexact=provider)

        if currency_code == '<currency_code>':
            # this is a link from the front page. we need to be selective around how we allow currency choice
            request_url = '{}://{}'.format(request.META.get('HTTP_X_FORWARDED_PROTO', 'http'), request.get_host())
            response = {}

            for currency in provider_obj.providerresponse_set.all(
            ).distinct(
                'currency'
            ).order_by(
                'currency'
            ).values_list(
                'currency__code',
                flat=True
            ):
                response[currency] = '{}/provider/{}/price/{}'.format(request_url, provider, currency)

            return JsonResponse(response, json_dumps_params={'sort_keys': True})

        # Bittrex still calls USNBT NBT!
        # TODO - handle multiple codes on model?
        if currency_code.lower() == 'nbt':
            currency_code = 'usnbt'

        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)

        # check the provider supports this currency
        if currency.code not in ProviderResponse.objects.filter(
            provider=provider_obj,
        ).values_list(
            'currency__code',
            flat=True
        ):
            return JsonResponse({'error': '{} is not supported by {}'.format(currency_code, provider)})

        # get the latest response
        last_response = provider_obj.providerresponse_set.filter(currency=currency).order_by('date_time').last()
        return JsonResponse(last_response.serialize())


class ProviderSpotPriceView(View):
    @staticmethod
    def get(request, provider, currency_code, date_time):
        if provider == '<provider>':
            return redirect(
                'provider_choose',
                path='{{}}|provider|{{}}|price|{currency_code}|<date_time>'.format(currency_code=currency_code)
            )

        provider_obj = get_object_or_404(Provider, name__iexact=provider)

        if currency_code == '<currency_code>':
            # this is a link from the front page. we need to be selective around how we allow currency choice
            request_url = '{}://{}'.format(request.META.get('HTTP_X_FORWARDED_PROTO', 'http'), request.get_host())
            response = {}

            for currency in provider_obj.providerresponse_set.all(
            ).distinct(
                'currency'
            ).order_by(
                'currency'
            ).values_list(
                'currency__code',
                flat=True
            ):
                response[currency] = '{}/provider/{}/price/{}/<date_time>'.format(request_url, provider, currency)

            return JsonResponse(response, json_dumps_params={'sort_keys': True})

        if date_time == '<date_time>':
            return JsonResponse(
                {'error': 'The date_time parameter needs to be passed in the format yyyy-mm-ddTHH:MM:SS'}
            )

        # Bittrex still calls USNBT NBT!
        # TODO - handle multiple codes on model?
        if currency_code.lower() == 'nbt':
            currency_code = 'usnbt'

        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)

        # check the provider supports this currency
        if currency.code not in ProviderResponse.objects.filter(
                provider=provider_obj,
        ).values_list(
            'currency__code',
            flat=True
        ):
            return JsonResponse({'error': '{} is not supported by {}'.format(currency_code, provider)})

        # get the datetime
        try:
            dt = make_aware(datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return JsonResponse(
                {'error': 'The date_time parameter needs to be passed in the format yyyy-mm-ddTHH:MM:SS'}
            )

        # get the aggregated price closest to date_time
        try:
            # get the closest response
            provider_response = ProviderResponse.objects.get_closest_to(
                provider=provider_obj,
                currency=currency,
                target=dt
            )
        except ProviderResponse.DoesNotExist:
            return JsonResponse(
                {'error': 'no provider response found'}
            )

        return JsonResponse(provider_response.serialize(), json_dumps_params={'sort_keys': True})


class PriceChangesView(View):
    @staticmethod
    def get(request, currency_code):
        if currency_code == '<currency_code>':
            # this is a link from the front page. Allow user to choose a currency code to select
            return redirect('currency_choose', path='{}|movement|{}')

        # Bittrex still calls USNBT NBT!
        # TODO - handle multiple codes on model?
        if currency_code.lower() == 'nbt':
            currency_code = 'usnbt'

        # get the currency
        currency = get_object_or_404(Currency, code__iexact=currency_code)

        return JsonResponse(currency.currency_movements())
