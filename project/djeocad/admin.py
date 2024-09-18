from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import Drawing, Layer


class LayerInline(admin.TabularInline):
    model = Layer
    fields = ("name", "color_field", "linetype")
    extra = 0


@admin.register(Drawing)
class DrawingAdmin(LeafletGeoAdmin):
    list_display = (
        "title",
        "epsg",
    )
    inlines = [
        LayerInline,
    ]
