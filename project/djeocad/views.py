from typing import Any

from django.conf import settings
from django.db.models.query import QuerySet
from django.views.generic import ListView

from .models import Drawing


class BaseListView(ListView):
    model = Drawing
    template_name = "djeocad/drawing_list.html"

    def get_queryset(self) -> QuerySet[Any]:
        qs = Drawing.objects.exclude(epsg=None)
        return qs

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["unreferenced"] = Drawing.objects.filter(epsg=None)
        context["leaflet_config"] = settings.LEAFLET_CONFIG
        return context
