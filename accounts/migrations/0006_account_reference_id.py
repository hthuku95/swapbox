# Generated by Django 4.0.3 on 2022-10-14 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_account_verified_and_securely_transfared'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='reference_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
