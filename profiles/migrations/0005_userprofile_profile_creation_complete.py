# Generated by Django 4.0.3 on 2022-10-19 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_wallet_alter_userprofile_profile_settings_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='profile_creation_complete',
            field=models.BooleanField(default=False),
        ),
    ]