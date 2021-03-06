import datetime
import math
from statistics import mean

from django.db import models
from django.utils.timezone import now


class Provider(models.Model):
    name = models.CharField(
        max_length=255,
        db_index=True
    )
    cache = models.IntegerField(
        default=300
    )
    active = models.BooleanField(
        default=True
    )
    exchange_provider = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name


class Currency(models.Model):
    code = models.CharField(
        max_length=10
    )
    name = models.CharField(
        max_length=255
    )
    min_providers = models.IntegerField(
        default=3
    )
    max_std_dev = models.IntegerField(
        default=60
    )

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

    class Meta:
        verbose_name_plural = 'Currencies'

    def currency_movements(self):
        """
        Calculate the movements in price between a range of times and now.
        expressed as percentage movement
        """
        # get the latest aggregated price
        latest_agg_price = self.aggregatedprice_set.order_by('date_time').last()

        movements = {
            'latest_price': float('{:.8f}'.format(latest_agg_price.aggregated_price)),
            'number_of_days': {}
        }

        for days in [1, 2, 3, 7, 14, 30]:
            price = self.aggregatedprice_set.get_closest_to(
                self,
                latest_agg_price.date_time - datetime.timedelta(days=days)
            )

            factor = ((latest_agg_price.aggregated_price - price.aggregated_price) / price.aggregated_price)

            movements['number_of_days'][days] = {
                'price': float('{:.8f}'.format(price.aggregated_price)),
                'movement_factor': float('{:.8f}'.format(1 + factor)),
                'movement_percentage': float('{:.8f}'.format(factor * 100))
            }

        return movements

    def arbitrage_opportunities(self):
        """
        Return a serialization of the last 10 arbitrage opportunities for this currency
        """
        return {
            'currency': self.code.upper(),
            'arbitrage_opportunities': [
                {
                    'date_time': op.date_time,
                    'low_exchange_pair': op.low_provider_response.provider.name,
                    'low_price': op.low_provider_response.value,
                    'high_exchange_pair': op.high_provider_response.provider.name,
                    'high_price': op.high_provider_response.value
                } for op in self.arbitrageopportunity_set.all()[:10]
            ]
        }


class ProviderBlackList(models.Model):
    currency = models.ForeignKey(
        'Currency',
        on_delete=models.CASCADE
    )
    provider = models.ForeignKey(
        'Provider',
        on_delete=models.CASCADE
    )


class ProviderResponseManager(models.Manager):
    def get_closest_to(self, provider, currency, target):
        closest_greater_qs = self.filter(
            provider=provider,
            currency=currency,
            date_time__gt=target
        ).order_by(
            'date_time'
        )

        closest_less_qs = self.filter(
            provider=provider,
            currency=currency,
            date_time__lt=target
        ).order_by(
            '-date_time'
        )

        try:
            try:
                closest_greater = closest_greater_qs[0]
            except IndexError:
                return closest_less_qs[0]

            try:
                closest_less = closest_less_qs[0]
            except IndexError:
                return closest_greater_qs[0]
        except IndexError:
            raise self.model.DoesNotExist(
                "There is no closest value because there are no values."
            )

        if closest_greater.date_time - target > target - closest_less.date_time:
            return closest_less
        else:
            return closest_greater


class ProviderResponse(models.Model):
    date_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        db_index=True
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        db_index=True
    )
    value = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=0
    )
    market_value = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=0
    )
    volume = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        blank=True,
        null=True
    )
    parent_response = models.ForeignKey(
        'ProviderResponse',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    update_by = models.DateTimeField(
        db_index=True
    )

    objects = ProviderResponseManager()

    def __str__(self):
        return '{} {}@{} ({})'.format(
            self.provider,
            self.currency,
            self.value,
            self.update_by
        )

    class Meta:
        ordering = ['-date_time']

    def calculate_moving_averages(self):
        """
        Get the previous 24 hours values and calculate various moving averages
        :return:
        """
        values = ProviderResponse.objects.filter(
            provider=self.provider,
            currency=self.currency,
            date_time__gt=(self.date_time - datetime.timedelta(hours=24))
        )

        if not values:
            return {}

        # calculate the moving averages
        moving_averages = {
            '30_minute': 30
        }

        for period in moving_averages.copy():
            agg_list = values.filter(
                date_time__gte=(self.date_time - datetime.timedelta(minutes=moving_averages[period]))
            ).values_list('value', flat=True)

            if len(agg_list) > 1:
                avg = mean(agg_list)

                if not math.isnan(avg):
                    moving_averages[period] = float('{:.8f}'.format(mean(agg_list)))
                else:
                    del moving_averages[period]
            else:
                del moving_averages[period]

        return moving_averages

    def serialize(self):
        serialized_data = {
            'provider': self.provider.name,
            'currency': self.currency.code,
            'currency_name': self.currency.name,
            'date_time': self.date_time,
            'usd_price': float('{:.8f}'.format(self.value)),
            'moving_averages': self.calculate_moving_averages()
        }

        if self.date_time < (now() - datetime.timedelta(hours=24)):
            serialized_data['warning'] = 'Price is older than 24 hours. Use with caution'

        if self.market_value is not None:
            serialized_data['market_price'] = float('{:.8f}'.format(self.market_value))

        if self.volume is not None:
            serialized_data['volume'] = float('{:.8f}'.format(self.volume))

        if self.providerresponse_set.all().count() > 0:
            serialized_data['combined_responses'] = [
                resp.serialize() for resp in self.providerresponse_set.all()
            ]

        return serialized_data


class ProviderFailure(models.Model):
    date_time = models.DateTimeField(
        auto_now_add=True
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE
    )
    message = models.TextField(
        blank=True,
        null=True
    )


class AggregatedPriceManager(models.Manager):
    def get_closest_to(self, currency, target):
        closest_greater_qs = self.filter(
            currency=currency,
            date_time__gt=target
        ).order_by(
            'date_time'
        )

        closest_less_qs = self.filter(
            currency=currency,
            date_time__lt=target
        ).order_by(
            '-date_time'
        )

        try:
            try:
                closest_greater = closest_greater_qs[0]
            except IndexError:
                return closest_less_qs[0]

            try:
                closest_less = closest_less_qs[0]
            except IndexError:
                return closest_greater_qs[0]
        except IndexError:
            raise self.model.DoesNotExist(
                "There is no closest value because there are no values."
            )

        if closest_greater.date_time - target > target - closest_less.date_time:
            return closest_less
        else:
            return closest_greater


class AggregatedPrice(models.Model):
    date_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE
    )
    aggregated_price = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        db_index=True
    )
    providers = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=0,
        db_index=True
    )
    standard_deviation = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=0
    )
    variance = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=0
    )
    used_responses = models.ManyToManyField(
        ProviderResponse
    )

    objects = AggregatedPriceManager()

    class Meta:
        ordering = ['-date_time']

    def calculate_moving_averages(self):
        """
        Get the previous 24 hours aggregated prices and calculate various moving averages
        :return:
        """
        agg_prices = AggregatedPrice.objects.filter(
            currency=self.currency,
            date_time__gt=(self.date_time - datetime.timedelta(hours=24))
        ).order_by(
            '-date_time'
        )

        if not agg_prices:
            return {}

        # calculate the moving averages
        moving_averages = {
            '24_hour': 1440,
            '12_hour': 720,
            '6_hour': 360,
            '1_hour': 60,
            '30_minute': 30
        }

        for period in moving_averages.copy():
            agg_list = agg_prices.filter(
                date_time__gte=(self.date_time - datetime.timedelta(minutes=moving_averages[period]))
            ).values_list('aggregated_price', flat=True)

            if len(agg_list) > 1:
                avg = mean(agg_list)

                if not math.isnan(avg):
                    moving_averages[period] = float('{:.8f}'.format(avg))
                else:
                    del moving_averages[period]
            else:
                del moving_averages[period]

        return moving_averages

    def serialize(self, style):
        serialized_data = {
            'currency': self.currency.code,
            'moving_averages': self.calculate_moving_averages(),
            'currency_name': self.currency.name,
            'aggregation_date_time': self.date_time,
            'aggregated_usd_price': float('{:.8f}'.format(self.aggregated_price)),
            'number_of_providers': float('{:.0f}'.format(self.providers)),
            'standard_deviation': float('{:.8f}'.format(self.standard_deviation)),
            'variance': float('{:.8f}'.format(self.variance))
        }

        if style == 'full':
            serialized_data['prices_used'] = [
                resp.serialize() for resp in self.used_responses.all()
            ]

        if self.date_time < (now() - datetime.timedelta(hours=24)):
            serialized_data['warning'] = 'Price is older than 24 hours. Use with caution'

        return serialized_data


class NuMarketMaker(models.Model):
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='currency',
        help_text='The currency to affect'
    )
    market_maker_price = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=1,
        help_text='the price to use in aggregation calculations'
    )
    market_target = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=1,
        help_text='The target to reach during increments.'
                  'If market_maker_price and this are equal, no more increments will take place'
    )
    market_movement = models.DecimalField(
        decimal_places=5,
        max_digits=25,
        default=0,
        help_text='The percentage movement that each increment will affect. Set to negative for downward movement'
    )
    multiplier = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='multiplier',
        blank=True,
        null=True,
        help_text='if this is set the market_maker_price will be multiplied by the latest aggregated price for this '
                  'currency before being used in Aggregation Calculations. '
                  'This effectively changes the market_maker_price to apply to this currency, '
                  'while still being priced in USD'
    )


class ArbitrageOpportunity(models.Model):
    date_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE
    )
    low_provider_response = models.ForeignKey(
        ProviderResponse,
        on_delete=models.CASCADE,
        related_name='low_provider_response'
    )
    high_provider_response = models.ForeignKey(
        ProviderResponse,
        on_delete=models.CASCADE,
        related_name='high_provider_response'
    )
    
    def __str__(self):
        return f'{self.date_time} - {self.currency}'

    class Meta:
        ordering = ['-date_time']


