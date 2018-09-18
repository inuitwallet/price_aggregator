from django.core.management import BaseCommand

from price_aggregator.models import NuMarketMaker


class Command(BaseCommand):
    def handle(self, *args, **options):
        # get the NuMarketMaker objects
        market_makers = NuMarketMaker.objects.all()

        for market_maker in market_makers:
            if market_maker.market_maker_price != market_maker.market_target:
                # price needs an increment
                increment = market_maker.market_maker_price * market_maker.market_movement
                print('Moving Market Maker for {} price by {} from {}'.format(
                    market_maker.currency.code,
                    increment,
                    market_maker.market_maker_price
                ))
                market_maker.market_maker_price += increment
                market_maker.save()

