# Generated by Django 5.1.1 on 2024-09-18 13:45

import django.db.models.deletion
import djgeojson.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("djeocad", "0003_layer"),
    ]

    operations = [
        migrations.CreateModel(
            name="Entity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data", models.JSONField(null=True)),
                ("geom", djgeojson.fields.GeometryCollectionField()),
                ("insertion", djgeojson.fields.PointField(null=True)),
                (
                    "layer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="related_entities",
                        to="djeocad.layer",
                    ),
                ),
            ],
            options={
                "verbose_name": "Entity",
                "verbose_name_plural": "Entities",
            },
        ),
    ]