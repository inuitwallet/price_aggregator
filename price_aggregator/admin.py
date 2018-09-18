from django.contrib import admin

from price_aggregator.models import Currency, Provider, AggregatedPrice, ProviderResponse, \
    ProviderFailure, ProviderBlackList, NuMarketMaker


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


@admin.register(ProviderBlackList)
class ProviderBlackList(admin.ModelAdmin):
    list_display = ['currency', 'provider']
    raw_id_fields = ['currency', 'provider']


@admin.register(NuMarketMaker)
class NuMarketMakerAdmin(admin.ModelAdmin):
    list_display = ['currency', 'market_maker_price']
    raw_id_fields = ['currency']
