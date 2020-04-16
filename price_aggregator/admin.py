from django.contrib import admin

from price_aggregator.models import Currency, Provider, AggregatedPrice, ProviderResponse, \
    ProviderFailure, ProviderBlackList, NuMarketMaker, ArbitrageOpportunity


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'cache', 'active', 'exchange_provider']
    list_editable = ['active', 'exchange_provider']
    list_filter = ['name']
    search_fields = ['name']


@admin.register(ProviderResponse)
class ProviderResponseAdmin(admin.ModelAdmin):
    list_display = ['date_time', 'provider', 'currency', 'value', 'volume', 'update_by']
    list_filter = ['provider', 'currency']
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
    list_display = ['currency', 'market_maker_price', 'market_target', 'market_movement', 'multiplier']
    list_editable = ['market_maker_price']
    raw_id_fields = ['currency', 'multiplier']


@admin.register(ArbitrageOpportunity)
class ArbitrageOpportunityAdmin(admin.ModelAdmin):
    list_display = ['date_time', 'currency', 'low_provider_response', 'high_provider_response']
    raw_id_fields = ['low_provider_response', 'high_provider_response']
