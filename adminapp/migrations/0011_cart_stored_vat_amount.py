# Generated by Django 5.1.4 on 2025-04-23 11:54

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0010_cart_applied_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='stored_vat_amount',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
