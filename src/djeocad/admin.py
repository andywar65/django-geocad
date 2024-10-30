from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.epsg:
            messages.add_message(
                request,
                messages.WARNING,
                _(
                    """GeoData missing. Upload a DXF with GeoData,
                    a Parent Drawing or select a Reference Point on the map"""
                ),
            )
