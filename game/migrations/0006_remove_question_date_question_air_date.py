# Generated by Django 4.2 on 2023-04-27 23:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_alter_player_options_alter_player_managers_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='date',
        ),
        migrations.AddField(
            model_name='question',
            name='air_date',
            field=models.DateField(default=None),
            preserve_default=False,
        ),
    ]