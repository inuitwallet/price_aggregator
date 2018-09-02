# Generated by Django 2.0.2 on 2018-09-01 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_aggregator', '0010_aggregatedprice_used_responses'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='max_std_dev',
            field=models.IntegerField(default=60),
        ),
        migrations.AddField(
            model_name='currency',
            name='min_providers',
            field=models.IntegerField(default=3),
        ),
    ]