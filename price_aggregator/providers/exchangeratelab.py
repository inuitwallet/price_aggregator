import logging
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ExchangeRateLab(object):
    """
    http://www.exchangeratelab.com
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('CryptoCompare: Getting prices')

        r = requests.get(
            url='http://api.exchangeratelab.com/api/current/USD?apikey={}'.format(
                settings.EXCHANGERATELAB_API_KEY
            )
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        try:
            data = r.json()
        except ValueError:
            return None, 'no json: {}'.format(r.text)

        #{"rates":[{"rate":1.2724,"to":"AUD"},{"rate":1.2454,"to":"CAD"},{"rate":6.3445,"to":"CNY"},{"rate":0.8375,"to":"EUR"},{"rate":0.7054,"to":"GBP"},{"rate":64.0630,"to":"INR"},{"rate":110.5096,"to":"JPY"},{"rate":1.0,"to":"USD"},{"rate":1.00,"to":"USD"}],"baseCurrency":"USD","timeStamp":1518652061,"executionTime":80,"licenseMessage":"Data Retrieved From www.ExchangeRateLab.com - Under license (Not for financial/professional use)"}

        rates = data.get('rates')

        if not rates:
            return None, 'no rates in data: {}'.format(data)

        search_codes = [coin.code.upper() for coin in currencies]
        output = {}

        for currency in rates:
            if currency.get('to') in search_codes:
                for coin in currencies:
                    if coin.code.upper() == currency.get('to'):
                        output[coin] = Decimal(1 / currency.get('rate'))

        return output, 'success'
