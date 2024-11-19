import csv
from typing import Any

from django.db.models.query import QuerySet
from django.forms import FloatField, ModelForm, NumberInput
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView

from .models import Drawing, Entity


class DrawingListView(ListView):
    model = Drawing
    template_name = "djeocad/drawing_list.html"

    def get_queryset(self) -> QuerySet[Any]:
        qs = Drawing.objects.exclude(epsg=None)
        return qs

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["unreferenced"] = Drawing.objects.filter(epsg=None)
        return context


class DrawingDetailView(DetailView):
    model = Drawing
    template_name = "djeocad/drawing_detail.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        layers = self.object.related_layers.filter(is_block=False)
        id_list = layers.values_list("id", flat=True)
        context["lines"] = Entity.objects.filter(
            layer_id__in=id_list
        ).prefetch_related()
        name_list = layers.values_list("name", flat=True)
        context["layer_list"] = list(dict.fromkeys(name_list))
        context["layer_list"] = [_("Layer - ") + s for s in context["layer_list"]]
        return context


class EntityCreateForm(ModelForm):
    lat = FloatField(
        label=_("Latitude"),
        widget=NumberInput(attrs={"max": 90, "min": -90}),
        required=True,
    )
    long = FloatField(
        label=_("Longitude"),
        widget=NumberInput(attrs={"max": 180, "min": -180}),
        required=True,
    )
    model = Entity
    fields = ["layer", "block", "rotation", "xscale", "yscale"]


class EntityCreateView(CreateView):
    model = Entity
    form_class = EntityCreateForm
    template_name = "djeocad/create_insertion.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.drawing = get_object_or_404(Drawing, id=request.GET["pk"])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        layers = self.drawing.related_layers.filter(is_block=False)
        id_list = layers.values_list("id", flat=True)
        context["lines"] = Entity.objects.filter(
            layer_id__in=id_list
        ).prefetch_related()
        name_list = layers.values_list("name", flat=True)
        context["layer_list"] = list(dict.fromkeys(name_list))
        context["layer_list"] = [_("Layer - ") + s for s in context["layer_list"]]
        return context


def csv_download(request, pk):
    drawing = get_object_or_404(Drawing, id=pk)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{drawing.title}.csv"'
    writer = csv.writer(response)
    writer = drawing.write_csv(writer)

    return response


def drawing_download(request, pk):
    drawing = get_object_or_404(Drawing, id=pk)
    response = HttpResponse(drawing.dxf, content_type="text/plain")
    response["Content-Disposition"] = f"attachment; filename={drawing.title}.dxf"

    return response
