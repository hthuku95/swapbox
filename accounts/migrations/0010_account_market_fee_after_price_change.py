# Generated by Django 4.0.3 on 2022-10-17 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_account_no_of_times_price_has_changed'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='market_fee_after_price_change',
            field=models.FloatField(blank=True, null=True),
        ),
    ]