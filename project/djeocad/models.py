import json
from math import atan2, degrees

import ezdxf
import nh3
from colorfield.fields import ColorField
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from djgeojson.fields import GeometryCollectionField, PointField
from ezdxf.addons import geo
from ezdxf.lldxf.const import InvalidGeoDataException
from ezdxf.math import Vec3
from pyproj import Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from shapely.geometry import shape


class Drawing(models.Model):

    title = models.CharField(
        _("Name"),
        help_text=_("Name of the drawing"),
        max_length=50,
    )
    dxf = models.FileField(
        _("DXF file"),
        max_length=200,
        upload_to="uploads/djeocad/dxf/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "dxf",
                ]
            )
        ],
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="parent_drawing",
        verbose_name=_("Parent Drawing"),
        null=True,
        blank=True,
    )
    image = models.ImageField(
        _("Image"), upload_to="uploads/djeocad/images/", null=True, blank=True
    )
    geom = PointField(_("Location"), null=True, blank=True)
    designx = models.FloatField(
        _("Design point X..."),
        default=0,
    )
    designy = models.FloatField(
        _("...Y"),
        default=0,
    )
    rotation = models.FloatField(
        _("Rotation"),
        default=0,
    )
    epsg = models.IntegerField(
        _("CRS code"),
        null=True,
        editable=False,
    )

    class Meta:
        verbose_name = _("Drawing")
        verbose_name_plural = _("Drawings")

    __original_dxf = None
    __original_geom = None
    __original_designx = None
    __original_designy = None
    __original_rotation = None
    # blacklists in settings
    layer_blacklist = settings.CAD_LAYER_BLACKLIST
    name_blacklist = settings.CAD_BLOCK_BLACKLIST
    entity_types = [
        "POINT",
        "LINE",
        "LWPOLYLINE",
        "POLYLINE",
        "3DFACE",
        "CIRCLE",
        "ARC",
        "ELLIPSE",
        "SPLINE",
        "HATCH",
    ]
    # TEXT overrides MTEXT
    text_types = [
        "MTEXT",
        "TEXT",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_dxf = self.dxf
        self.__original_geom = self.geom
        self.__original_designx = self.designx
        self.__original_designy = self.designy
        self.__original_rotation = self.rotation

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # save and eventually upload DXF
        super().save(*args, **kwargs)
        # check if we have coordinate system
        if not self.epsg:
            # check if user has inserted parent
            if self.parent:
                self.geom = self.parent.geom
                self.epsg = self.parent.epsg
                self.designx = self.parent.designx
                self.designy = self.parent.designy
                self.rotation = self.parent.rotation
                super().save(*args, **kwargs)
                # we have eveything we need, go ahead!
                # extract_dxf(self, doc=None, refresh=True)
                return
            # check if user has inserted origin on map
            elif self.geom:
                # following conditional for test to work
                if isinstance(self.geom, str):
                    self.geom = json.loads(self.geom)
                # let's find proper UTM
                utm_crs_list = query_utm_crs_info(
                    datum_name="WGS 84",
                    area_of_interest=AreaOfInterest(
                        west_lon_degree=self.geom["coordinates"][0],
                        south_lat_degree=self.geom["coordinates"][1],
                        east_lon_degree=self.geom["coordinates"][0],
                        north_lat_degree=self.geom["coordinates"][1],
                    ),
                )
                self.epsg = utm_crs_list[0].code
                super().save(*args, **kwargs)
                # we have eveything we need, go ahead!
                # extract_dxf(self, doc=None, refresh=True)
                return
            # no user input, search for geodata in dxf
            else:
                doc = ezdxf.readfile(self.dxf.path)
                msp = doc.modelspace()
                geodata = msp.get_geodata()
                if geodata:
                    # check if valid XML and axis order
                    try:
                        self.epsg, axis = geodata.get_crs()
                        if not axis:
                            return
                    except InvalidGeoDataException:
                        return
                    utm2world = Transformer.from_crs(self.epsg, 4326, always_xy=True)
                    world_point = utm2world.transform(
                        geodata.dxf.reference_point[0], geodata.dxf.reference_point[1]
                    )
                    self.geom = {"type": "Point", "coordinates": world_point}
                    self.designx = geodata.dxf.design_point[0]
                    self.designy = geodata.dxf.design_point[1]
                    self.rotation = degrees(
                        atan2(
                            geodata.dxf.north_direction[0],
                            geodata.dxf.north_direction[1],
                        )
                    )
                    super().save(*args, **kwargs)
                    # we have eveything we need, go ahead!
                    # extract_dxf(self, doc)
                return
        # check if something changed
        if (
            self.__original_dxf != self.dxf
            or self.__original_geom != self.geom
            or self.__original_designx != self.designx
            or self.__original_designy != self.designy
            or self.__original_rotation != self.rotation
        ):
            pass
            # all_layers = self.related_layers.all()
            # if all_layers.exists():
            #   all_layers.delete()
            # extract_dxf(self, doc=None, refresh=True)


class Layer(models.Model):

    drawing = models.ForeignKey(
        Drawing,
        on_delete=models.CASCADE,
        related_name="related_layers",
        verbose_name=_("Drawing"),
    )
    name = models.CharField(
        _("Layer name"),
        max_length=50,
    )
    color_field = ColorField(default="#FFFFFF")
    linetype = models.BooleanField(
        _("Continuous linetype"),
        default=True,
    )
    is_block = models.BooleanField(
        default=False,
        editable=False,
    )
    geom = GeometryCollectionField(
        null=True,
    )

    class Meta:
        verbose_name = _("Layer")
        verbose_name_plural = _("Layers")
        ordering = ("name",)


class Entity(models.Model):

    layer = models.ForeignKey(
        Layer,
        on_delete=models.CASCADE,
        related_name="related_entities",
    )
    data = models.JSONField(
        null=True,
    )
    geom = GeometryCollectionField()
    insertion = PointField(
        null=True,
    )

    class Meta:
        verbose_name = _("Entity")
        verbose_name_plural = _("Entities")

    @property
    def popupContent(self):
        if self.layer.is_block:
            ltype = _("Block")
        else:
            ltype = _("Layer")
        title_str = f"<p>{ltype}: {nh3.clean(self.layer.name)}</p>"
        data = ""
        if self.data:
            data = f"<ul><li>ID = {self.id}</li>"
            for k, v in self.data.items():
                if k == "attributes":
                    continue
                data += f"<li>{k} = {nh3.clean(str(v))}</li>"
            data += "</ul>"
            if "attributes" in self.data:
                data += "<p>Attributes</p><ul>"
                for k, v in self.data["attributes"].items():
                    data += f"<li>{nh3.clean(str(k))} = {nh3.clean(str(v))}</li>"
                data += "</ul>"
        return {
            "content": title_str + data,
            "color": self.layer.color_field,
            "linetype": self.layer.linetype,
            "layer": _("Layer - ") + nh3.clean(self.layer.name),
        }


"""
    Collection of utilities
"""


def cad2hex(color):
    if isinstance(color, tuple):
        return "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
    rgb24 = ezdxf.colors.DXF_DEFAULT_COLORS[color]
    return "#{:06X}".format(rgb24)


def get_geo_proxy(entity, matrix, transformer):
    geo_proxy = geo.proxy(entity)
    if geo_proxy.geotype == "Polygon":
        if not shape(geo_proxy).is_valid:
            return False
    geo_proxy.wcs_to_crs(matrix)
    geo_proxy.apply(lambda v: Vec3(transformer.transform(v.x, v.y)))
    return geo_proxy
