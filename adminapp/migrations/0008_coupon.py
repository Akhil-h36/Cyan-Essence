# Generated by Django 5.1.4 on 2025-04-21 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0007_alter_offertable_discount_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coupon_code', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], max_length=20)),
                ('discount_value', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('min_order_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('max_discount_value', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('valid_from', models.DateTimeField()),
                ('valid_to', models.DateTimeField()),
                ('usage_limit', models.PositiveIntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=False)),
            ],
        ),
    ]
