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

    def serialize(self):
        return {
            'currency': self.currency.code,
            'aggregation_date_time': self.date_time,
            'aggregated_usd_price': self.aggregated_price,
            'number_of_providers': self.providers,
            'standard_deviation': self.standard_deviation,
            'variance': self.variance
        }








