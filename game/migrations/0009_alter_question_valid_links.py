# Generated by Django 5.0.4 on 2024-05-16 23:39

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_question_valid_links'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='valid_links',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=250), default=list, size=3),
        ),
    ]