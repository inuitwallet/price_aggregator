# Generated by Django 2.0.2 on 2018-02-14 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price_aggregator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
