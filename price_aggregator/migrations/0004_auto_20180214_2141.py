# Generated by Django 2.0.2 on 2018-02-14 21:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_aggregator', '0003_auto_20180214_2125'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aggregatedprice',
            name='confidence',
        ),
        migrations.AddField(
            model_name='aggregatedprice',
            name='variance',
            field=models.DecimalField(decimal_places=10, default=0, max_digits=25),
        ),
        migrations.AlterField(
            model_name='aggregatedprice',
            name='standard_deviation',
            field=models.DecimalField(decimal_places=10, default=0, max_digits=25),
        ),
    ]
