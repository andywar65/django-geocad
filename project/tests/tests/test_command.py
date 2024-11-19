from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings

from djeocad.models import Drawing, Entity, Layer


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT).joinpath("tests"))
@override_settings(DEBUG=True)
class GeoCADCommandTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        dxf_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/nogeo.dxf")
        with open(dxf_path, "rb") as f:
            content = f.read()
        draw1 = Drawing()
        draw1.title = "Not referenced"
        draw1.dxf = SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf")
        draw1.save()
        layer = Layer.objects.create(drawing=draw1, name="Lajer")
        block = Layer.objects.create(drawing=draw1, name="Bloke", is_block=True)
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
            data={"Foo": "Bar"},
        )
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
            insertion={"type": "Point", "coordinates": [12.523826, 41.90339]},
            data={"Block": block.name, "X scale": 2, "attributes": {"Faz": "Baz"}},
        )

    @classmethod
    def tearDownClass(cls):
        """Checks existing files, then removes them"""
        try:
            path = Path(settings.MEDIA_ROOT).joinpath("uploads/djeocad/dxf/")
            list = [e for e in path.iterdir() if e.is_file()]
            for file in list:
                Path(file).unlink()
        except FileNotFoundError:
            pass

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "populate_block_field",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_command(self):
        self.call_command()
        block = Layer.objects.get(name="Bloke")
        for ent in Entity.objects.all():
            self.assertTrue("processed" in ent.data)
            if "Block" in ent.data and ent.data["Block"] == "Bloke":
                self.assertEqual(ent.block, block)
                self.assertEqual(ent.xscale, 2)
                for e in ent.related_data.all():
                    self.assertEqual(e.key, "Faz")
                    self.assertEqual(e.value, "Baz")
