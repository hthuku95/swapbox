# Generated by Django 4.0.3 on 2022-10-17 11:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_alter_order_payment_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_type',
            field=models.CharField(blank=True, choices=[('AU', 'Account Upload'), ('AP', 'Account Purchase'), ('PC', 'Price Change')], max_length=2, null=True),
        ),
    ]
