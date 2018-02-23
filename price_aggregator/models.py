from django.db import models


class Provider(models.Model):
    name = models.CharField(
        max_length=255
    )
    cache = models.IntegerField(
        default=300
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

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

    class Meta:
        verbose_name_plural = 'Currencies'


class ProviderResponse(models.Model):
    date_time = models.DateTimeField(
        auto_now_add=True
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE
    )
    value = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=0
    )
    update_by = models.DateTimeField()

    def __str__(self):
        return '{} {}@{} ({})'.format(
            self.provider,
            self.currency,
            self.value,
            self.update_by
        )


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


class AggregatedPrice(models.Model):
    date_time = models.DateTimeField(
        auto_now_add=True
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE
    )
    aggregated_price = models.DecimalField(
        decimal_places=10,
        max_digits=25
    )
    providers = models.DecimalField(
        decimal_places=10,
        max_digits=25,
        default=0
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

    def serialize(self):
        return {
            'currency': self.currency.code,
            'currency_name': self.currency.name,
            'aggregation_date_time': self.date_time,
            'aggregated_usd_price': float('{:.8f}'.format(self.aggregated_price)),
            'number_of_providers': float('{:.0f}'.format(self.providers)),
            'standard_deviation': float('{:.8f}'.format(self.standard_deviation)),
            'variance': float('{:.8f}'.format(self.variance)),
            'prices_used': [
                {
                    'name': resp.provider.name,
                    'value': float('{:.8f}'.format(resp.value)),
                    'collection_date_time': resp.date_time,
                    'cache_seconds': float('{:0f}'.format(resp.provider.cache))
                } for resp in self.used_responses.all()
            ]
        }








