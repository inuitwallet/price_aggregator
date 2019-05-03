import xml.etree.ElementTree as etree
import logging
from decimal import Decimal
import requests

logger = logging.getLogger(__name__)


class EcbEuropa(object):
    """
    http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
    """
    @staticmethod
    def get_prices(currencies):
        logger.info('EcbEuropa: Getting prices')

        r = requests.get(
            url='http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
        )

        if r.status_code != requests.codes.ok:
            return None, 'bad status code: {}'.format(r.status_code)

        tree = etree.fromstring(r.content)
        cube = None

        for elem in tree:
            if 'Cube' in elem.tag:
                cube = elem

        if not cube:
            return None, 'no \'Cube\' found in xml content'

        # These rates are in EUR so we need to get the USD rate first
        usd_rate = 1

        for child in cube[0]:
            if child.attrib.get('currency') == 'USD':
                usd_rate = Decimal(child.attrib.get('rate'))

        search_codes = [coin.code.upper() for coin in currencies]
        output = []

        for child in cube[0]:
            if child.attrib.get('currency') in search_codes:
                for coin in currencies:
                    if coin.code.upper() == child.attrib.get('currency'):
                        output.append(
                            {
                                'coin': coin,
                                'price': Decimal(1 / (Decimal(child.attrib.get('rate')) * usd_rate))
                            }
                        )

        return output, 'success'
