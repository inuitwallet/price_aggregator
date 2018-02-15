from django.contrib import admin

from price_aggregator.models import Currency, Provider, AggregatedPrice, ProviderResponse, \
    ProviderFailure


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'cache']


@admin.register(ProviderResponse)
class ProviderResponseAdmin(admin.ModelAdmin):
    list_display = ['date_time', 'provider', 'currency', 'value', 'update_by']
    raw_id_fields = ['provider', 'currency']


@admin.register(ProviderFailure)
class ProviderFailureAdmin(admin.ModelAdmin):
    list_display = ['date_time', 'provider', 'message']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']


@admin.register(AggregatedPrice)
class AggregatedPriceAdmin(admin.ModelAdmin):
    list_display = ['date_time', 'currency', 'aggregated_price']
    raw_id_fields = ['currency']
