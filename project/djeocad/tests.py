from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import Drawing, Entity, Layer


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT).joinpath("tests"))
class GeoCADModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        dxf_path = Path(settings.BASE_DIR).joinpath(
            "djeocad/static/djeocad/tests/nogeo.dxf"
        )
        with open(dxf_path, "rb") as f:
            content = f.read()
        draw1 = Drawing()
        draw1.title = "Not referenced"
        draw1.dxf = SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf")
        draw1.save()
        dxf_path = Path(settings.BASE_DIR).joinpath(
            "djeocad/static/djeocad/tests/yesgeo.dxf"
        )
        with open(dxf_path, "rb") as f:
            content = f.read()
        draw2 = Drawing()
        draw2.title = "Referenced"
        draw2.dxf = SimpleUploadedFile("yesgeo.dxf", content, "image/x-dxf")
        draw2.save()
        layer = Layer.objects.create(drawing=draw2, name="Layer")
        Entity.objects.create(
            layer=layer,
            geom={
                "type": "GeometryCollection",
                "geometries": [
                    {
                        "type": "LineString",
                        "coordinates": [
                            [[12.523826, 41.90339], [12.523826, 41.903391]]
                        ],
                    }
                ],
            },
        )

    def tearDown(self):
        """Checks existing files, then removes them.
        Not working for filer paths"""
        try:
            path = Path(settings.MEDIA_ROOT).joinpath("uploads/djeocad/dxf/")
            list = [e for e in path.iterdir() if e.is_file()]
            for file in list:
                Path(file).unlink()
        except FileNotFoundError:
            pass

    def test_drawing_str_method(self):
        draw = Drawing.objects.get(title="Not referenced")
        self.assertEqual(draw.__str__(), "Not referenced")

    def test_drawing_epsg_none(self):
        draw = Drawing.objects.get(title="Not referenced")
        self.assertEqual(draw.epsg, None)

    def test_drawing_geom_none(self):
        draw = Drawing.objects.get(title="Not referenced")
        self.assertEqual(draw.geom, None)

    def test_drawing_epsg_none_set_geom(self):
        draw = Drawing.objects.get(title="Not referenced")
        draw.geom = {"type": "Point", "coordinates": [120.48, 42.00]}
        draw.save()
        self.assertEqual(int(draw.epsg), 32651)  # why string?

    def test_drawing_epsg_none_set_parent(self):
        draw = Drawing.objects.get(title="Not referenced")
        parent = Drawing.objects.get(title="Referenced")
        draw.parent = parent
        draw.save()
        self.assertEqual(draw.epsg, 32633)

    def test_drawing_epsg_yes(self):
        draw = Drawing.objects.get(title="Referenced")
        self.assertEqual(draw.epsg, 32633)

    def test_drawing_geom_yes(self):
        draw = Drawing.objects.get(title="Referenced")
        self.assertEqual(draw.geom["coordinates"][0], 12.48293852819188)

    def test_drawing_epsg_yes_set_geom(self):
        draw = Drawing.objects.get(title="Referenced")
        draw.geom = {"type": "Point", "coordinates": [120.48, 42.00]}
        draw.save()
        # not implemented, should be 32651
        self.assertEqual(int(draw.epsg), 32633)  # why string?
