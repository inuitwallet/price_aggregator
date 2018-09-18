import logging

from price_aggregator.models import NuMarketMaker

logger = logging.getLogger(__name__)


class Nu(object):
    """
    Nu intent for weighting Nubits
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('Nu: Getting prices')

        output = {}

        for currency in currencies:
            if currency.code in ['USNBT', 'CNNBT', 'EUNBT', 'XNBT']:
                try:
                    maker_price = NuMarketMaker.objects.get(currency=currency).market_maker_price
                except NuMarketMaker.DoesNotExist:
                    continue

                output[currency] = maker_price

        return output, 'success'


