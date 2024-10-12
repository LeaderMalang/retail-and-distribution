# Generated by Django 4.2.16 on 2024-10-12 13:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_accounttransaction_purchaseorder_supplier_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinancialReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_type', models.CharField(max_length=255)),
                ('generated_date', models.DateField(auto_now_add=True)),
                ('content', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='GeneralLedger',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_name', models.CharField(max_length=255)),
                ('balance', models.DecimalField(decimal_places=2, max_digits=15)),
            ],
        ),
        migrations.CreateModel(
            name='InventoryBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_number', models.CharField(max_length=50)),
                ('expiration_date', models.DateField()),
                ('quantity', models.IntegerField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.product')),
            ],
        ),
        migrations.CreateModel(
            name='AccountReceivable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=15)),
                ('due_date', models.DateField()),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.customer')),
            ],
        ),
        migrations.CreateModel(
            name='AccountPayable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_due', models.DecimalField(decimal_places=2, max_digits=15)),
                ('due_date', models.DateField()),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.supplier')),
            ],
        ),
    ]