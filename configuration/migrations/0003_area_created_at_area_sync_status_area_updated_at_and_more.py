# Generated by Django 4.2.16 on 2024-11-12 19:34

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0002_bookingman_sales_commission_bookingman_sales_target_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2024, 11, 12, 19, 33, 27, 139440, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='area',
            name='sync_status',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='area',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='bookingman',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2024, 11, 12, 19, 33, 30, 275464, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bookingman',
            name='sync_status',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bookingman',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='city',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2024, 11, 12, 19, 33, 32, 563073, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='city',
            name='sync_status',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='city',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]