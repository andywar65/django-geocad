from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Drawing, Entity, Layer, cad2hex


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
        img_path = Path(settings.BASE_DIR).joinpath(
            "djeocad/static/djeocad/tests/image.jpg"
        )
        with open(img_path, "rb") as fi:
            img_content = fi.read()
        draw2 = Drawing()
        draw2.title = "Referenced"
        draw2.dxf = SimpleUploadedFile("yesgeo.dxf", content, "image/x-dxf")
        draw2.image = SimpleUploadedFile("image.jpg", img_content, "image/jpeg")
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
        try:
            path = Path(settings.MEDIA_ROOT).joinpath("uploads/djeocad/images/")
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
        doc = draw.get_geodata_from_dxf()
        self.assertFalse(doc)

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
        self.assertIsNone(draw.parent)

    def test_get_geodata_from_parent(self):
        draw = Drawing.objects.get(title="Not referenced")
        parent = Drawing.objects.get(title="Referenced")
        draw.parent = parent
        draw.get_geodata_from_parent()
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
        self.assertEqual(int(draw.epsg), 32651)  # why string?

    def test_get_geodata_from_geom(self):
        draw = Drawing.objects.get(title="Referenced")
        draw.geom = {"type": "Point", "coordinates": [120.48, 42.00]}
        draw.get_geodata_from_geom()
        self.assertEqual(int(draw.epsg), 32651)  # why string?

    def test_get_geodata_from_dxf_yes(self):
        draw = Drawing.objects.get(title="Referenced")
        doc = draw.get_geodata_from_dxf()
        self.assertIsNotNone(doc)

    def test_drawing_popup(self):
        draw = Drawing.objects.get(title="Not referenced")
        popup = {
            "content": f'<a href="/geocad/{draw.id}"><strong>{draw.title}</strong></a>',
        }
        self.assertEqual(draw.popupContent, popup)

    def test_drawing_popup_image(self):
        draw = Drawing.objects.get(title="Referenced")
        string = (
            '<img src="/media/uploads/djeocad/images/image.jpg.256x192_q85_crop.jpg">'
        )
        string += f'<br><a href="/geocad/{draw.id}"><strong>{draw.title}</strong></a>'
        popup = {
            "content": string,
        }
        self.assertEqual(draw.popupContent, popup)

    def test_entity_popup(self):
        layer = Layer.objects.get(name="Layer")
        ent = Entity.objects.get(layer=layer)
        popup = {
            "content": "<p>Layer: Layer</p>",
            "color": "#FFFFFF",
            "linetype": True,
            "layer": "Layer - Layer",
        }
        self.assertEqual(ent.popupContent, popup)

    def test_entity_popup_is_block(self):
        layer = Layer.objects.get(name="Layer")
        layer.is_block = True
        layer.save()
        ent = Entity.objects.get(layer=layer)
        popup = {
            "content": "<p>Block: Layer</p>",
            "color": "#FFFFFF",
            "linetype": True,
            "layer": "Layer - Layer",
        }
        self.assertEqual(ent.popupContent, popup)

    def test_entity_popup_layer_name_bleach(self):
        layer = Layer.objects.get(name="Layer")
        layer.name = "<scrip>alert('hello')</script>"
        layer.save()
        ent = Entity.objects.get(layer=layer)
        popup = {
            "content": "<p>Layer: alert('hello')</p>",
            "color": "#FFFFFF",
            "linetype": True,
            "layer": "Layer - alert('hello')",
        }
        self.assertEqual(ent.popupContent, popup)

    def test_entity_popup_data(self):
        layer = Layer.objects.get(name="Layer")
        ent = Entity.objects.get(layer=layer)
        ent.data = {"foo": "bar"}
        ent.save()
        data = f"<ul><li>ID = {ent.id}</li>"
        data += "<li>foo = bar</li></ul>"
        popup = {
            "content": "<p>Layer: Layer</p>" + data,
            "color": "#FFFFFF",
            "linetype": True,
            "layer": "Layer - Layer",
        }
        self.assertEqual(ent.popupContent, popup)

    def test_entity_popup_data_bleach(self):
        layer = Layer.objects.get(name="Layer")
        ent = Entity.objects.get(layer=layer)
        ent.data = {"foo": "<scrip>alert('hello')</script>"}
        ent.save()
        data = f"<ul><li>ID = {ent.id}</li>"
        data += "<li>foo = alert('hello')</li></ul>"
        popup = {
            "content": "<p>Layer: Layer</p>" + data,
            "color": "#FFFFFF",
            "linetype": True,
            "layer": "Layer - Layer",
        }
        self.assertEqual(ent.popupContent, popup)

    def test_entity_popup_data_attributes(self):
        layer = Layer.objects.get(name="Layer")
        ent = Entity.objects.get(layer=layer)
        ent.data = {"attributes": {"foo": "bar"}}
        ent.save()
        data = f"<ul><li>ID = {ent.id}</li></ul>"
        data += "<p>Attributes</p><ul>"
        data += "<li>foo = bar</li></ul>"
        popup = {
            "content": "<p>Layer: Layer</p>" + data,
            "color": "#FFFFFF",
            "linetype": True,
            "layer": "Layer - Layer",
        }
        self.assertEqual(ent.popupContent, popup)

    def test_room_entity_popup(self):
        draw = Drawing.objects.get(title="Referenced")
        one = Layer.objects.get(drawing=draw, name="one")
        ent = Entity.objects.get(layer=one, data__Name="Room")
        self.assertEqual(ent.popupContent["color"], one.color_field)
        self.assertEqual(ent.popupContent["layer"], f"Layer - {one.name}")
        self.assertIn(f"<p>Layer: {one.name}</p>", ent.popupContent["content"])
        self.assertIn(f"<li>ID = {ent.id}</li>", ent.popupContent["content"])
        self.assertIn(
            f"<li>Name = {ent.data['Name']}</li>", ent.popupContent["content"]
        )
        self.assertIn(
            f"<li>Surface = {ent.data['Surface']}</li>", ent.popupContent["content"]
        )
        self.assertIn(
            f"<li>Height = {ent.data['Height']}</li>", ent.popupContent["content"]
        )
        self.assertIn(
            f"<li>Perimeter = {ent.data['Perimeter']}</li>", ent.popupContent["content"]
        )

    def test_cad2hex_tuple(self):
        color = (128, 128, 128)
        self.assertEqual(cad2hex(color), "#808080")

    def test_cad2hex_default(self):
        color = 128
        self.assertEqual(cad2hex(color), "#00261C")

    def test_drawing_list_view_status_code(self):
        response = self.client.get(
            reverse(
                "djeocad:drawing_list",
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_drawing_detail_view_status_code(self):
        draw = Drawing.objects.get(title="Referenced")
        response = self.client.get(
            reverse("djeocad:drawing_detail", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_drawing_csv_view_status_code(self):
        draw = Drawing.objects.get(title="Referenced")
        response = self.client.get(
            reverse("djeocad:drawing_csv", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_drawing_download_view_status_code(self):
        draw = Drawing.objects.get(title="Referenced")
        response = self.client.get(
            reverse("djeocad:drawing_download", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_drawing_list_view_template(self):
        response = self.client.get(
            reverse(
                "djeocad:drawing_list",
            )
        )
        self.assertTemplateUsed(response, "djeocad/drawing_list.html")

    def test_drawing_detail_view_template(self):
        draw = Drawing.objects.get(title="Referenced")
        response = self.client.get(
            reverse("djeocad:drawing_detail", kwargs={"pk": draw.id})
        )
        self.assertTemplateUsed(response, "djeocad/drawing_detail.html")

    def test_drawing_list_view_unreferenced_in_context(self):
        response = self.client.get(
            reverse(
                "djeocad:drawing_list",
            )
        )
        self.assertTrue("unreferenced" in response.context)

    def test_drawing_list_view_unreferenced_length(self):
        response = self.client.get(
            reverse(
                "djeocad:drawing_list",
            )
        )
        self.assertEqual(len(response.context["unreferenced"]), 1)

    def test_drawing_detail_view_lines_in_context(self):
        draw = Drawing.objects.get(title="Referenced")
        response = self.client.get(
            reverse("djeocad:drawing_detail", kwargs={"pk": draw.id})
        )
        self.assertTrue("lines" in response.context)
        self.assertTrue("layer_list" in response.context)

    def test_drawing_detail_view_lines_length(self):
        draw = Drawing.objects.get(title="Referenced")
        response = self.client.get(
            reverse("djeocad:drawing_detail", kwargs={"pk": draw.id})
        )
        self.assertEqual(len(response.context["lines"]), 5)
        self.assertEqual(len(response.context["layer_list"]), 4)
