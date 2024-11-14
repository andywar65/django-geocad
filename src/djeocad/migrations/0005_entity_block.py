# Generated by Django 5.1.1 on 2024-11-14 17:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("djeocad", "0004_entity"),
    ]

    operations = [
        migrations.AddField(
            model_name="entity",
            name="block",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="related_insertions",
                to="djeocad.layer",
            ),
        ),
    ]
