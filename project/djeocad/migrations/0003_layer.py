# Generated by Django 5.1.1 on 2024-09-18 13:36

import colorfield.fields
import django.db.models.deletion
import djgeojson.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("djeocad", "0002_alter_drawing_options_drawing_designx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Layer",
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
                ("name", models.CharField(max_length=50, verbose_name="Layer name")),
                (
                    "color_field",
                    colorfield.fields.ColorField(
                        default="#FFFFFF", image_field=None, max_length=25, samples=None
                    ),
                ),
                (
                    "linetype",
                    models.BooleanField(
                        default=True, verbose_name="Continuous linetype"
                    ),
                ),
                ("is_block", models.BooleanField(default=False, editable=False)),
                ("geom", djgeojson.fields.GeometryCollectionField(null=True)),
                (
                    "drawing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="related_layers",
                        to="djeocad.drawing",
                        verbose_name="Drawing",
                    ),
                ),
            ],
            options={
                "verbose_name": "Layer",
                "verbose_name_plural": "Layers",
                "ordering": ("name",),
            },
        ),
    ]