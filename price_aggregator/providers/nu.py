import logging

from price_aggregator.models import NuMarketMaker, AggregatedPrice

logger = logging.getLogger(__name__)


class Nu(object):
    """
    Nu intent for weighting Nubits
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Nu: Getting prices')

        output = []

        for currency in currencies:
            if currency.code in ['USNBT', 'CNNBT', 'EUNBT', 'XNBT']:
                try:
                    maker = NuMarketMaker.objects.get(currency=currency)
                except NuMarketMaker.DoesNotExist:
                    continue

                multiplier_price = 1

                if maker.multiplier:
                    multiplier = AggregatedPrice.objects.filter(currency=maker.multiplier).first()
                    if multiplier:
                        multiplier_price = multiplier.aggregated_price

                output.append(
                    {
                        'coin': currency,
                        'price': maker.market_maker_price * multiplier_price
                    }
                )

        return output, 'success'


