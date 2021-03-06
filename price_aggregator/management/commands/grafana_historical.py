import datetime
import pickle
import socket
import struct
from statistics import mean

from django.core.management import BaseCommand
from django.utils.timezone import make_aware

from price_aggregator.models import AggregatedPrice, Currency


class Command(BaseCommand):
    def send_to_carbon(self, carbon_data):
        payload = pickle.dumps(carbon_data, protocol=2)
        header = struct.pack("!L", len(payload))
        message = header + payload

        try:
            carbon_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            carbon_socket.connect(
                ('grafana.crypto-daio.co.uk', 2004)
            )
            data_sent = carbon_socket.send(message)
            carbon_socket.close()
            return data_sent
        except socket.gaierror as e:
            print(e)
            return 0

    def handle(self, *args, **options):
        start_date = make_aware(datetime.datetime(2018, 7, 5, 8, 00))
        end_date = make_aware(datetime.datetime(2018, 10, 30, 23, 40))

        while start_date < end_date:
            carbon_data = []

            for currency in Currency.objects.all():
                try:
                    agg_price = AggregatedPrice.objects.get_closest_to(
                        currency=currency,
                        target=start_date
                    )
                except AggregatedPrice.DoesNotExist:
                    continue

                # agg_prices = AggregatedPrice.objects.filter(
                #     currency=currency,
                #     date_time__gt=agg_price.date_time - datetime.timedelta(minutes=30)
                # ).values_list('aggregated_price', flat=True)
                #
                # if len(agg_prices) > 1:
                #     min_30_price = float('{:.8f}'.format(mean(agg_prices)))
                # else:
                #     min_30_price = None

                price = float('{:.8f}'.format(agg_price.aggregated_price))
                timestamp = int(start_date.timestamp())

                print('{} = {} @ {}'.format(currency, price, timestamp))

                carbon_data.append(
                    (
                        'lambda.currencies.{}.aggregator_price'.format(
                            currency.code.upper()
                        ),
                        (timestamp, str(price))
                    )
                )

                carbon_data.append(
                    (
                        'lambda.currencies.{}.aggregator_variance'.format(
                            currency.code.upper()
                        ),
                        (timestamp, str(agg_price.variance))
                    )
                )

                carbon_data.append(
                    (
                        'lambda.currencies.{}.aggregator_stdev'.format(
                            currency.code.upper()
                        ),
                        (timestamp, str(agg_price.standard_deviation))
                    )
                )

                carbon_data.append(
                    (
                        'lambda.currencies.{}.aggregator_number_of_providers'.format(
                            currency.code.upper()
                        ),
                        (timestamp, str(float('{:.0f}'.format(agg_price.providers))))
                    )
                )

                # if min_30_price:
                #     carbon_data.append(
                #         (
                #             'lambda.currencies.{}.aggregator_30_minute_ma'.format(
                #                 currency.code.upper()
                #             ),
                #             (timestamp, str(min_30_price))
                #         )
                #     )

            self.send_to_carbon(carbon_data)

            start_date += datetime.timedelta(minutes=5)
