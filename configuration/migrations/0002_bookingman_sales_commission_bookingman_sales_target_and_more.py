# Generated by Django 4.2.16 on 2024-10-26 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookingman',
            name='sales_commission',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='bookingman',
            name='sales_target',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='bookingman',
            name='targeted_month',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='bookingman',
            name='total_sales',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
