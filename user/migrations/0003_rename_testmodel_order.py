# Generated by Django 5.1.4 on 2025-04-09 04:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_auto_20250409_1024'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='testmodel',
            new_name='order',
        ),
    ]
