from math import atan2, cos, degrees, radians, sin

import ezdxf
import nh3
from colorfield.fields import ColorField
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djgeojson.fields import GeometryCollectionField, PointField
from easy_thumbnails.files import get_thumbnailer
from ezdxf.addons import geo
from ezdxf.lldxf.const import InvalidGeoDataException
from pyproj import Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from shapely.geometry import Point, shape
from shapely.geometry.polygon import Polygon


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

    def get_absolute_url(self):
        return reverse("djeocad:drawing_detail", kwargs={"pk": self.id})

    @property
    def popupContent(self):
        url = self.get_absolute_url()
        title_str = f'<a href="{url}"><strong>{self.title}</strong></a>'
        image = self.image
        if not image:
            return {"content": title_str}
        thumbnailer = get_thumbnailer(image)
        thumb = thumbnailer.get_thumbnail({"size": (256, 192), "crop": True})
        image_str = '<img src="%(image)s">' % {"image": thumb.url}
        return {"content": image_str + "<br>" + title_str}

    def save(self, *args, **kwargs):
        # save and eventually upload DXF
        super().save(*args, **kwargs)
        # check if we have coordinate system
        if not self.epsg:
            # check if user has inserted parent
            if self.parent:
                self.get_geodata_from_parent(*args, **kwargs)
                self.extract_dxf(doc=None, refresh=True)
                return
            # check if user has inserted origin on map
            elif self.geom:
                self.get_geodata_from_geom(*args, **kwargs)
                self.extract_dxf(doc=None, refresh=True)
                return
            # no user input, search for geodata in dxf
            else:
                doc = self.get_geodata_from_dxf(*args, **kwargs)
                # if successful use geodata
                if doc:
                    self.extract_dxf(doc)
                return
        # ok, we have coordinate system
        # check if user has inserted new parent
        if self.parent:
            self.delete_all_layers()
            self.get_geodata_from_parent(*args, **kwargs)
            self.extract_dxf(doc=None, refresh=True)
            return
        # check if user has modified origin on map
        if self.geom and self.__original_geom != self.geom:
            self.delete_all_layers()
            self.get_geodata_from_geom(*args, **kwargs)
            self.extract_dxf(doc=None, refresh=True)
            return
        # check if user changed dxf
        if self.__original_dxf != self.dxf:
            self.delete_all_layers()
            doc = self.get_geodata_from_dxf(*args, **kwargs)
            # if successful use new geodata
            if doc:
                self.extract_dxf(doc)
            # else use old geodata
            elif self.geom:
                self.extract_dxf(doc=None, refresh=True)
            return
        # check if something else changed
        if (
            self.__original_designx != self.designx
            or self.__original_designy != self.designy
            or self.__original_rotation != self.rotation
        ):
            self.delete_all_layers()
            self.extract_dxf(doc=None, refresh=True)

    def delete_all_layers(self):
        all_layers = self.related_layers.all()
        if all_layers.exists():
            all_layers.delete()

    def get_geodata_from_parent(self, *args, **kwargs):
        self.geom = self.parent.geom
        self.epsg = self.parent.epsg
        self.designx = self.parent.designx
        self.designy = self.parent.designy
        self.rotation = self.parent.rotation
        self.parent = None
        super().save(*args, **kwargs)

    def get_geodata_from_geom(self, *args, **kwargs):
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

    def get_geodata_from_dxf(self, *args, **kwargs):
        doc = ezdxf.readfile(self.dxf.path)
        msp = doc.modelspace()
        geodata = msp.get_geodata()
        if geodata:
            # check if valid XML and axis order
            try:
                self.epsg, axis = geodata.get_crs()
                if not axis:
                    return False
            except InvalidGeoDataException:
                return False
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
            return doc
        return False

    def extract_dxf(self, doc=None, refresh=False):
        # prepare transformers
        world2utm, utm2world, utm_wcs, rot = self.prepare_transformers()
        # get DXF if none
        if not doc:
            doc = ezdxf.readfile(self.dxf.path)
        msp = doc.modelspace()
        geodata = msp.get_geodata()
        if not geodata or refresh:
            # faking geodata
            geodata = msp.new_geodata()
            geodata = self.fake_geodata(geodata, utm_wcs, rot)
            # replace stored DXF
            doc.saveas(filename=self.dxf.path, encoding="utf-8", fmt="asc")
        # get transform matrix from true or fake geodata
        m, epsg = geodata.get_crs_transformation(no_checks=True)  # noqa
        layer_table = self.prepare_layer_table(doc)
        for e_type in self.entity_types:
            self.extract_entities(msp, e_type, m, utm2world, layer_table)
        self.create_layer_entities(layer_table)
        self.save_blocks(doc, m, utm2world)
        # extract insertions
        for ins in msp.query("INSERT"):
            self.extract_insertions(ins, msp, m, utm2world, layer_table)

    def prepare_transformers(self):
        world2utm = Transformer.from_crs(4326, self.epsg, always_xy=True)
        utm2world = Transformer.from_crs(self.epsg, 4326, always_xy=True)
        utm_wcs = world2utm.transform(
            self.geom["coordinates"][0], self.geom["coordinates"][1]
        )
        rot = radians(self.rotation)
        return world2utm, utm2world, utm_wcs, rot

    def fake_geodata(self, geodata, utm_wcs, rot):
        geodata.coordinate_system_definition = self.get_epsg_xml()
        geodata.dxf.design_point = (self.designx, self.designy, 0)
        geodata.dxf.reference_point = utm_wcs
        geodata.dxf.north_direction = (sin(rot), cos(rot))
        return geodata

    def get_epsg_xml(self):
        xml = """<?xml version="1.0"
encoding="UTF-16" standalone="no" ?>
<Dictionary version="1.0" xmlns="http://www.osgeo.org/mapguide/coordinatesystem">
<Alias id="%(epsg)s" type="CoordinateSystem">
<ObjectId>EPSG=%(epsg)s</ObjectId>
<Namespace>EPSG Code</Namespace>
</Alias>
<Axis uom="METER">
<CoordinateSystemAxis>
<AxisOrder>1</AxisOrder>
<AxisName>Easting</AxisName>
<AxisAbbreviation>E</AxisAbbreviation>
<AxisDirection>east</AxisDirection>
</CoordinateSystemAxis>
<CoordinateSystemAxis>
<AxisOrder>2</AxisOrder>
<AxisName>Northing</AxisName>
<AxisAbbreviation>N</AxisAbbreviation>
<AxisDirection>north</AxisDirection>
</CoordinateSystemAxis>
</Axis>
</Dictionary>""" % {
            "epsg": self.epsg
        }
        return xml

    def prepare_layer_table(self, doc):
        layer_table = {}
        for layer in doc.layers:
            if layer.dxf.name in self.layer_blacklist:
                continue
            if layer.rgb:
                color = cad2hex(layer.rgb)
            else:
                color = cad2hex(layer.color)
            layer_obj = Layer.objects.create(
                drawing_id=self.id,
                name=layer.dxf.name,
                color_field=color,
            )
            layer_table[layer.dxf.name] = {
                "layer_obj": layer_obj,
                "geometries": [],
            }
        return layer_table

    def extract_entities(self, msp, e_type, m, utm2world, layer_table):
        for e in msp.query(e_type):
            geo_proxy = get_geo_proxy(e, m, utm2world)
            if geo_proxy:
                if e_type in ["LWPOLYLINE", "POLYLINE"]:
                    entity_data = {}
                    # check if it's a true polygon
                    try:
                        poly = Polygon(e.vertices_in_wcs())
                        # look for texts in same layer
                        for t_type in self.text_types:
                            txts = msp.query(f"{t_type}[layer=='{e.dxf.layer}']")
                            for t in txts:
                                point = Point(t.dxf.insert)
                                # check if text is contained by polygon
                                if poly.contains(point):
                                    # handle different type of texts
                                    if t_type == "TEXT":
                                        entity_data["Name"] = t.dxf.text
                                    else:
                                        entity_data["Name"] = t.text
                                    break
                        if e.is_closed:
                            entity_data["Surface"] = round(poly.area, 2)
                        if e.dxf.thickness:
                            entity_data["Height"] = round(e.dxf.thickness, 2)
                        entity_data["Perimeter"] = round(poly.length, 2)
                        if e.dxf.const_width:
                            entity_data["Width"] = round(e.dxf.const_width, 2)
                        Entity.objects.create(
                            layer=layer_table[e.dxf.layer]["layer_obj"],
                            geom={
                                "geometries": [geo_proxy.__geo_interface__],
                                "type": "GeometryCollection",
                            },
                            data=entity_data,
                        )
                    except (AttributeError, ValueError):
                        # not true polygon, add to layer entity
                        layer_table[e.dxf.layer]["geometries"].append(
                            geo_proxy.__geo_interface__
                        )
                else:
                    # not polyline, add to layer entity
                    layer_table[e.dxf.layer]["geometries"].append(
                        geo_proxy.__geo_interface__
                    )

    def create_layer_entities(self, layer_table):
        for name, layer_data in layer_table.items():
            # next conditional is true TDD!
            if len(layer_data["geometries"]) == 0:
                continue
            Entity.objects.create(
                layer=layer_data["layer_obj"],
                geom={
                    "geometries": layer_data["geometries"],
                    "type": "GeometryCollection",
                },
            )

    def save_blocks(self, doc, m, utm2world):
        for block in doc.blocks:
            if block.name in self.name_blacklist:
                continue
            geometries = []
            for e_type in self.entity_types:
                # extract entities
                for e in block.query(e_type):
                    geo_proxy = get_geo_proxy(e, m, utm2world)
                    if geo_proxy:
                        geometries.append(geo_proxy.__geo_interface__)
            # create block as Layer
            if not geometries == []:
                Layer.objects.create(
                    drawing_id=self.id,
                    name=block.name,
                    geom={
                        "geometries": geometries,
                        "type": "GeometryCollection",
                    },
                    is_block=True,
                )

    def extract_insertions(self, ins, msp, m, utm2world, layer_table):
        # filter blacklisted blocks
        if ins.dxf.name in self.name_blacklist:
            return
        point = msp.add_point(ins.dxf.insert)
        geo_proxy = get_geo_proxy(point, m, utm2world)
        if geo_proxy:
            insertion_point = geo_proxy.__geo_interface__
        geometries = []
        # 'generator' object has no attribute 'query'
        for e in ins.virtual_entities():
            if e.dxftype() in self.entity_types:
                # extract entity
                geo_proxy = get_geo_proxy(e, m, utm2world)
                if geo_proxy:
                    geometries.append(geo_proxy.__geo_interface__)
        # prepare block data
        data_ins = {}
        data_ins["Block"] = ins.dxf.name
        if ins.dxf.rotation:
            data_ins["Rotation"] = round(ins.dxf.rotation, 2)
        if ins.dxf.xscale:
            data_ins["X scale"] = round(ins.dxf.xscale, 2)
        if ins.dxf.yscale:
            data_ins["Y scale"] = round(ins.dxf.yscale, 2)
        if ins.attribs:
            attrib_dict = {}
            for attr in ins.attribs:
                attrib_dict[attr.dxf.tag] = attr.dxf.text
            data_ins["attributes"] = attrib_dict
        # create Insertion
        Entity.objects.create(
            data=data_ins,
            layer=layer_table[ins.dxf.layer]["layer_obj"],
            insertion=insertion_point,
            geom={
                "geometries": geometries,
                "type": "GeometryCollection",
            },
        )

    def write_csv(self, writer):
        writer_data = []
        layers = self.related_layers.all()
        for layer in layers:
            entities = layer.related_entities.exclude(data=None)
            for e in entities:
                entity_data = {
                    "id": e.id,
                    "layer": layer.name,
                    "data": e.data,
                }
                if e.insertion:
                    entity_data["Latitude"] = e.insertion["coordinates"][0]
                    entity_data["Longitude"] = e.insertion["coordinates"][1]
                writer_data.append(entity_data)
        writer.writerow(
            [
                _("ID"),
                _("Layer"),
                _("Block"),
                _("Name"),
                _("Surface"),
                _("Perimeter"),
                _("Height"),
                _("Width"),
                _("Rotation"),
                _("X scale"),
                _("Y scale"),
                _("Latitude"),
                _("Longitude"),
                _("Attributes"),
            ]
        )
        keys = [
            "Block",
            "Name",
            "Surface",
            "Perimeter",
            "Height",
            "Width",
            "Rotation",
            "X scale",
            "Y scale",
        ]
        for wd in writer_data:
            row = []
            row.append(wd["id"])
            row.append(wd["layer"])
            for k in keys:
                if k in wd["data"]:
                    row.append(wd["data"][k])
                else:
                    row.append("")
            if "Latitude" in wd:
                row.append(wd["Latitude"])
            else:
                row.append("")
            if "Longitude" in wd:
                row.append(wd["Longitude"])
            else:
                row.append("")
            if "attributes" in wd["data"]:
                for attr, value in wd["data"]["attributes"].items():
                    row.append(attr)
                    row.append(value)
            writer.writerow(row)
        return writer


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
    block = models.ForeignKey(
        Layer,
        on_delete=models.CASCADE,
        related_name="related_insertions",
        null=True,
    )
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


class EntityData(models.Model):

    entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="related_data",
    )
    key = models.CharField(
        _("Data key"),
        max_length=50,
    )
    value = models.CharField(
        _("Data value"),
        max_length=100,
    )

    class Meta:
        verbose_name = _("Entity Data")
        verbose_name_plural = _("Entity Data")


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
    geo_proxy.apply(lambda v: ezdxf.math.Vec3(transformer.transform(v.x, v.y)))
    return geo_proxy
