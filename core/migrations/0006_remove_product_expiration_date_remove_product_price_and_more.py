# Generated by Django 4.2.16 on 2024-10-14 18:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_inventorybatch_purchase_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='expiration_date',
        ),
        migrations.RemoveField(
            model_name='product',
            name='price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='quantity',
        ),
    ]