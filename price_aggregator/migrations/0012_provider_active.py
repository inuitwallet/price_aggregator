# Generated by Django 2.0.2 on 2018-09-01 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_aggregator', '0011_auto_20180901_1832'),
    ]

    operations = [
        migrations.AddField(
            model_name='provider',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]