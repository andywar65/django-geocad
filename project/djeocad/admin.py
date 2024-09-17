from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import Drawing


@admin.register(Drawing)
class DrawingAdmin(LeafletGeoAdmin):
    list_display = (
        "title",
        "epsg",
    )
