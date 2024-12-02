import csv
from typing import Any

from django.contrib.auth.decorators import permission_required
from django.db.models.query import QuerySet
from django.forms import FloatField, ModelForm, NumberInput
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from .models import Drawing, Entity, EntityData


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
        if self.object.related_layers.filter(is_block=True).exists():
            context["blocks"] = True
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

    class Meta:
        model = Entity
        fields = ["layer", "block", "rotation", "xscale", "yscale"]

    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data["lat"]
        long = cleaned_data["long"]
        if lat > 90 or lat < -90:
            self.add_error("lat", _("Invalid value"))
        if long > 180 or long < -180:
            self.add_error("long", _("Invalid value"))
        return cleaned_data


@permission_required("djeocad.change_drawing")
def add_block_insertion(request, pk):
    drawing = get_object_or_404(Drawing, id=pk)
    blocks = drawing.related_layers.filter(is_block=True)
    if not blocks.exists():
        raise Http404
    layers = drawing.related_layers.filter(is_block=False)
    context = {}
    if request.POST:
        form = EntityCreateForm(request.POST)
        if form.is_valid():
            ent = Entity(
                layer=form.cleaned_data["layer"],
                block=form.cleaned_data["block"],
                rotation=form.cleaned_data["rotation"],
                xscale=form.cleaned_data["xscale"],
                yscale=form.cleaned_data["yscale"],
                insertion={
                    "type": "Point",
                    "coordinates": [
                        form.cleaned_data["long"],
                        form.cleaned_data["lat"],
                    ],
                },
                data={
                    "processed": "true",
                    "added": "true",
                },
            )
            ent.save()
            return HttpResponseRedirect(
                reverse("djeocad:insertion_change", kwargs={"pk": ent.id})
            )
    else:
        form = EntityCreateForm(
            initial={
                "rotation": 0,
                "xscale": 1,
                "yscale": 1,
                "lat": drawing.geom["coordinates"][1],
                "long": drawing.geom["coordinates"][0],
            }
        )
    form.fields["layer"].queryset = layers
    form.fields["block"].queryset = blocks
    context["form"] = form
    id_list = layers.values_list("id", flat=True)
    context["lines"] = Entity.objects.filter(layer_id__in=id_list).prefetch_related()
    name_list = layers.values_list("name", flat=True)
    context["layer_list"] = list(dict.fromkeys(name_list))
    context["layer_list"] = [_("Layer - ") + s for s in context["layer_list"]]
    context["drawing"] = drawing
    return TemplateResponse(request, "djeocad/entity_create.html", context)


@permission_required("djeocad.change_drawing")
def change_block_insertion(request, pk):
    object = get_object_or_404(Entity, id=pk)
    drawing = object.layer.drawing
    blocks = drawing.related_layers.filter(is_block=True)
    if not blocks.exists():
        raise Http404
    layers = drawing.related_layers.filter(is_block=False)
    context = {}
    if request.POST:
        form = EntityCreateForm(request.POST)
        if form.is_valid():
            object.layer = form.cleaned_data["layer"]
            object.block = form.cleaned_data["block"]
            object.rotation = form.cleaned_data["rotation"]
            object.xscale = form.cleaned_data["xscale"]
            object.yscale = form.cleaned_data["yscale"]
            object.insertion = {
                "type": "Point",
                "coordinates": [
                    form.cleaned_data["long"],
                    form.cleaned_data["lat"],
                ],
            }
            object.save()
            return HttpResponseRedirect(
                reverse("djeocad:drawing_detail", kwargs={"pk": drawing.id})
            )
    else:
        form = EntityCreateForm(
            initial={
                "layer": object.layer,
                "block": object.block,
                "rotation": object.rotation,
                "xscale": object.xscale,
                "yscale": object.yscale,
                "lat": object.insertion["coordinates"][1],
                "long": object.insertion["coordinates"][0],
            }
        )
    form.fields["layer"].queryset = layers
    form.fields["block"].queryset = blocks
    context["form"] = form
    id_list = layers.values_list("id", flat=True)
    context["lines"] = Entity.objects.filter(layer_id__in=id_list).prefetch_related()
    name_list = layers.values_list("name", flat=True)
    context["layer_list"] = list(dict.fromkeys(name_list))
    context["layer_list"] = [_("Layer - ") + s for s in context["layer_list"]]
    context["drawing"] = drawing
    context["object"] = object
    context["related_data"] = object.related_data.all()
    context["data_form"] = EntityDataForm()
    return TemplateResponse(request, "djeocad/entity_change.html", context)


@permission_required("djeocad.change_drawing")
def delete_block_insertion(request, pk):
    object = get_object_or_404(Entity, id=pk)
    drawing = object.layer.drawing
    object.delete()
    return HttpResponseRedirect(
        reverse("djeocad:drawing_detail", kwargs={"pk": drawing.id})
    )


class EntityDataListView(ListView):
    model = EntityData
    template_name = "djeocad/htmx/entity_data_list.html"
    context_object_name = "related_data"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.entity = get_object_or_404(Entity, id=kwargs["pk"])

    def get_queryset(self):
        return EntityData.objects.filter(entity=self.entity)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["object"] = self.entity
        context["data_form"] = EntityDataForm()
        return context


class EntityDataForm(ModelForm):
    class Meta:
        model = EntityData
        fields = ["key", "value"]


@permission_required("djeocad.change_drawing")
def create_entity_data(request, pk):
    if (
        "Hx-Request" not in request.headers
        or not request.headers["Hx-Request"] == "true"
    ):
        raise Http404
    entity = get_object_or_404(Entity, id=pk)
    if request.POST:
        form = EntityDataForm(request.POST)
        if form.is_valid():
            EntityData.objects.create(
                entity=entity,
                key=form.cleaned_data["key"],
                value=form.cleaned_data["value"],
            )
            return HttpResponseRedirect(
                reverse("djeocad:data_list", kwargs={"pk": entity.id})
            )


@permission_required("djeocad.change_drawing")
def delete_entity_data(request, pk):
    if (
        "Hx-Request" not in request.headers
        or not request.headers["Hx-Request"] == "true"
    ):
        raise Http404
    object = get_object_or_404(EntityData, id=pk)
    entity = object.entity
    object.delete()
    return HttpResponseRedirect(reverse("djeocad:data_list", kwargs={"pk": entity.id}))


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
    drawing.prepare_dxf_to_download()
    response = HttpResponse(drawing.dxf, content_type="text/plain")
    response["Content-Disposition"] = f"attachment; filename={drawing.title}.dxf"

    return response
