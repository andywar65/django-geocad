from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin

from .models import Drawing, Layer


class LayerInline(admin.TabularInline):
    model = Layer
    fields = ("name", "color_field", "linetype")
    extra = 0

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(is_block=True)


@admin.register(Drawing)
class DrawingAdmin(LeafletGeoAdmin):
    list_display = (
        "title",
        "epsg",
    )
    inlines = [
        LayerInline,
    ]
