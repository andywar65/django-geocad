# Generated by Django 5.1.1 on 2024-11-14 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("djeocad", "0006_entitydata"),
    ]

    operations = [
        migrations.AddField(
            model_name="entity",
            name="rotation",
            field=models.FloatField(default=0, verbose_name="Rotation"),
        ),
        migrations.AddField(
            model_name="entity",
            name="xscale",
            field=models.FloatField(default=1, verbose_name="X scale"),
        ),
        migrations.AddField(
            model_name="entity",
            name="yscale",
            field=models.FloatField(default=1, verbose_name="Y scale"),
        ),
    ]