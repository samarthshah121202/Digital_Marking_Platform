# Generated by Django 5.1.3 on 2024-11-13 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_studentwork_first_name_studentwork_last_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='is_group_assignment',
            field=models.BooleanField(default=False),
        ),
    ]
