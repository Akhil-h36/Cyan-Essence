# Generated by Django 5.1.4 on 2025-04-09 05:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0002_cart_cartitem'),
        ('user', '0004_remove_order_firstname_order_cancel_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='orderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_returned', models.BooleanField(default=False)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('return_reason', models.TextField(blank=True, null=True)),
                ('return_status', models.CharField(blank=True, choices=[('Requested', 'Return Requested'), ('Approved', 'Return Approved'), ('Rejected', 'Return Rejected'), ('Completed', 'Return Completed')], max_length=20, null=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='user.order')),
                ('product_variation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='adminapp.variencetable')),
            ],
        ),
    ]
