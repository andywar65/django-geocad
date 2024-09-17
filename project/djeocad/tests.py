from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import Drawing


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

    def test_drawing_epsg_yes(self):
        draw = Drawing.objects.get(title="Referenced")
        self.assertEqual(draw.epsg, 32633)
