# Generated by Django 5.1.1 on 2024-11-19 18:52

import djgeojson.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("django_geocad", "0008_alter_entity_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entity",
            name="geom",
            field=djgeojson.fields.GeometryCollectionField(null=True),
        ),
    ]
