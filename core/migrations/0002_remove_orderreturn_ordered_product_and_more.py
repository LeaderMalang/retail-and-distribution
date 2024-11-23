# Generated by Django 4.2.16 on 2024-11-03 18:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderreturn',
            name='ordered_product',
        ),
        migrations.RemoveField(
            model_name='orderreturn',
            name='quantity_returned',
        ),
        migrations.AddField(
            model_name='orderreturn',
            name='order',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='returns', to='core.order'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='orderreturn',
            name='reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderreturn',
            name='refund_status',
            field=models.CharField(choices=[('REFUNDED', 'REFUNDED'), ('PARTIALLY REFUNDED', 'PARTIALLY REFUNDED')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='orderreturn',
            name='returned_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='orderreturn',
            name='total_return_amount',
            field=models.DecimalField(decimal_places=2, default='1', max_digits=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Returned', 'Returned')], max_length=50),
        ),
        migrations.AlterField(
            model_name='orderreturn',
            name='return_date',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.CreateModel(
            name='OrderReturnProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('returned_quantity', models.PositiveIntegerField(default=0)),
                ('order_return', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='returned_products', to='core.orderreturn')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.product')),
            ],
        ),
    ]