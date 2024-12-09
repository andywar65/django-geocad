from pathlib import Path
from unittest import skip

import ezdxf
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from pyproj import Transformer

from djeocad.models import Drawing, Entity, EntityData, Layer, cad2hex
from djeocad.views import EntityCreateForm


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT).joinpath("tests"))
class GeoCADModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        dxf_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/nogeo.dxf")
        with open(dxf_path, "rb") as f:
            content = f.read()
        draw1 = Drawing()
        draw1.title = "Unreferenced"
        draw1.dxf = SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf")
        draw1.save()
        dxf_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/yesgeo.dxf")
        with open(dxf_path, "rb") as f:
            content = f.read()
        img_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/image.jpg")
        with open(img_path, "rb") as fi:
            img_content = fi.read()
        draw2 = Drawing()
        draw2.title = "Referenced"
        draw2.dxf = SimpleUploadedFile("yesgeo.dxf", content, "image/x-dxf")
        draw2.image = SimpleUploadedFile("image.jpg", img_content, "image/jpeg")
        draw2.save()
        User.objects.create_superuser("boss", "test@example.com", "p4s5w0r6")
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

    def test_geocad_manager_group_exists(self):
        self.assertTrue(Group.objects.filter(name="GeoCAD Manager").exists())

    def test_drawing_str_method(self):
        draw = Drawing.objects.get(title="Unreferenced")
        self.assertEqual(draw.__str__(), "Unreferenced")

    def test_drawing_epsg_none(self):
        draw = Drawing.objects.get(title="Unreferenced")
        self.assertEqual(draw.epsg, None)

    def test_drawing_geom_none(self):
        draw = Drawing.objects.get(title="Unreferenced")
        self.assertEqual(draw.geom, None)

    def test_drawing_epsg_none_set_geom(self):
        draw = Drawing.objects.get(title="Unreferenced")
        draw.geom = {"type": "Point", "coordinates": [120.48, 42.00]}
        draw.save()
        self.assertEqual(int(draw.epsg), 32651)  # why string?

    def test_drawing_epsg_none_set_parent(self):
        draw = Drawing.objects.get(title="Unreferenced")
        parent = Drawing.objects.get(title="Referenced")
        draw.parent = parent
        draw.save()
        self.assertEqual(draw.epsg, 32633)
        self.assertIsNone(draw.parent)

    def test_drawing_epsg_none_set_new_parent(self):
        draw = Drawing.objects.get(title="Unreferenced")
        parent = Drawing.objects.get(title="Referenced")
        draw.parent = parent
        draw.save()
        self.assertIsNone(draw.parent)
        draw.parent = parent
        draw.save()
        self.assertIsNone(draw.parent)

    def test_drawing_change_dxf_no_geodata(self):
        draw = Drawing.objects.get(title="Referenced")
        dxf_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/nogeo.dxf")
        with open(dxf_path, "rb") as f:
            content = f.read()
        draw.dxf = SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf")
        draw.save()
        self.assertEqual(draw.epsg, 32633)

    def test_drawing_change_dxf_with_geodata(self):
        draw = Drawing.objects.get(title="Referenced")
        dxf_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/yesgeo.dxf")
        with open(dxf_path, "rb") as f:
            content = f.read()
        draw.dxf = SimpleUploadedFile("yesgeo.dxf", content, "image/x-dxf")
        draw.save()
        self.assertEqual(draw.epsg, 32633)

    def test_drawing_change_design_point(self):
        draw = Drawing.objects.get(title="Referenced")
        draw.designx = 1
        draw.save()
        self.assertEqual(draw.epsg, 32633)

    def test_delete_all_layers(self):
        draw = Drawing.objects.get(title="Referenced")
        self.assertTrue(draw.related_layers.all().exists())
        draw.delete_all_layers()
        self.assertFalse(draw.related_layers.all().exists())

    def test_get_geodata_from_parent(self):
        draw = Drawing.objects.get(title="Unreferenced")
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

    def test_prepare_transformers(self):
        draw = Drawing.objects.get(title="Referenced")
        world2utm, utm2world, utm_wcs, rot = draw.prepare_transformers()
        self.assertEqual(
            world2utm, Transformer.from_crs(4326, draw.epsg, always_xy=True)
        )
        self.assertEqual(
            utm2world, Transformer.from_crs(draw.epsg, 4326, always_xy=True)
        )
        self.assertAlmostEqual(utm_wcs[0], 291187.7155651262)
        self.assertAlmostEqual(utm_wcs[1], 4640994.318375054)
        self.assertEqual(rot, 0)

    def test_fake_geodata(self):
        draw = Drawing.objects.get(title="Unreferenced")
        draw.epsg = 32633
        draw.geom = {"type": "Point", "coordinates": [12.0, 42.0]}
        doc = ezdxf.readfile(draw.dxf.path)
        msp = doc.modelspace()
        geodata = msp.new_geodata()
        world2utm, utm2world, utm_wcs, rot = draw.prepare_transformers()
        geodata = draw.fake_geodata(geodata, utm_wcs, rot)
        self.assertIsInstance(geodata, ezdxf.entities.geodata.GeoData)
        self.assertEqual(geodata.dxf.design_point, (0, 0, 0))
        self.assertAlmostEqual(geodata.dxf.reference_point[0], 251535.07928761785)
        self.assertAlmostEqual(geodata.dxf.reference_point[1], 4654130.8913233075)
        self.assertEqual(geodata.dxf.north_direction[1], 1)

    def test_get_epsg_xml(self):
        draw = Drawing.objects.get(title="Referenced")
        xml = draw.get_epsg_xml()
        self.assertIn(f'<Alias id="{draw.epsg}" type="CoordinateSystem">', xml)
        self.assertIn(f"<ObjectId>EPSG={draw.epsg}</ObjectId>", xml)

    def test_prepare_layer_table(self):
        draw = Drawing.objects.get(title="Unreferenced")
        doc = ezdxf.readfile(draw.dxf.path)
        layer_table = draw.prepare_layer_table(doc)
        self.assertEqual(len(layer_table), 2)
        self.assertEqual(layer_table["0"]["geometries"], [])
        self.assertEqual(layer_table["one"]["layer_obj"].drawing_id, draw.id)
        self.assertEqual(layer_table["one"]["layer_obj"].name, "one")
        self.assertEqual(layer_table["one"]["layer_obj"].color_field, "#FF0000")

    def test_extract_entities(self):
        draw = Drawing.objects.get(title="Referenced")
        doc = ezdxf.readfile(draw.dxf.path)
        msp = doc.modelspace()
        geodata = msp.get_geodata()
        m, epsg = geodata.get_crs_transformation(no_checks=True)
        world2utm, utm2world, utm_wcs, rot = draw.prepare_transformers()
        layer_table = draw.prepare_layer_table(doc)
        ent = Entity.objects.last()
        self.assertTrue("processed" in ent.data)
        e_type = "LWPOLYLINE"
        draw.extract_entities(msp, e_type, m, utm2world, layer_table)
        ent = Entity.objects.last()
        ent_data = ent.related_data.all()
        for ed in ent_data:
            if ed.key == "Name":
                self.assertTrue(ed.value in ["A", "Room"])

    def test_create_layer_entities(self):
        draw = Drawing.objects.get(title="Referenced")
        doc = ezdxf.readfile(draw.dxf.path)
        msp = doc.modelspace()
        geodata = msp.get_geodata()
        m, epsg = geodata.get_crs_transformation(no_checks=True)
        world2utm, utm2world, utm_wcs, rot = draw.prepare_transformers()
        layer_table = draw.prepare_layer_table(doc)
        ent = Entity.objects.last()
        self.assertEqual(ent.layer.name, "Layer")
        e_type = "LINE"
        draw.extract_entities(msp, e_type, m, utm2world, layer_table)
        draw.create_layer_entities(layer_table)
        ent = Entity.objects.last()
        self.assertEqual(ent.layer.name, "rgb")

    def test_save_blocks(self):
        # TODO make this test more meaningful
        draw = Drawing.objects.get(title="Referenced")
        doc = ezdxf.readfile(draw.dxf.path)
        msp = doc.modelspace()
        geodata = msp.get_geodata()
        m, epsg = geodata.get_crs_transformation(no_checks=True)
        world2utm, utm2world, utm_wcs, rot = draw.prepare_transformers()
        blk_before = Layer.objects.filter(is_block=True).count()
        draw.save_blocks(doc, m, utm2world)
        blk_after = Layer.objects.filter(is_block=True).count()
        self.assertEqual(blk_after - blk_before, 0)

    def test_extract_insertions(self):
        draw = Drawing.objects.get(title="Referenced")
        doc = ezdxf.readfile(draw.dxf.path)
        msp = doc.modelspace()
        geodata = msp.get_geodata()
        m, epsg = geodata.get_crs_transformation(no_checks=True)
        world2utm, utm2world, utm_wcs, rot = draw.prepare_transformers()
        layer_table = draw.prepare_layer_table(doc)
        block_table = draw.save_blocks(doc, m, utm2world)
        ins_before = Entity.objects.exclude(block=None).count()
        ins = msp.query("INSERT")[0]
        draw.extract_insertions(ins, msp, m, utm2world, layer_table, block_table)
        ins_after = Entity.objects.exclude(block=None).count()
        self.assertTrue(ins_after - ins_before, 1)

    def test_entity_save_method(self):
        draw = Drawing.objects.get(title="Referenced")
        layer = Layer.objects.get(drawing=draw, name="0")
        block = Layer.objects.filter(drawing=draw, is_block=True).last()
        self.assertEqual(block.name, "block")
        ent = Entity.objects.create(
            layer=layer,
            block=block,
            insertion={"type": "Point", "coordinates": [12.48, 42.00]},
            data={
                "processed": "true",
                "added": "true",
            },
        )
        self.assertIn("geometries", ent.geom)
        ent_data = ent.related_data.all()
        self.assertEqual(ent_data.count(), 1)
        for ed in ent_data:
            self.assertEqual(ed.key, "TAG")
            self.assertEqual(ed.value, "Tag")
        ent2 = Entity.objects.create(
            layer=layer,
            block=block,
            insertion={"type": "Point", "coordinates": [12.48, 42.00]},
        )
        self.assertIsNone(ent2.geom)

    def test_drawing_popup(self):
        draw = Drawing.objects.get(title="Unreferenced")
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
        self.assertIn(f"<p>ID = {ent.id}</p>", ent.popupContent["content"])
        self.assertIn("<ul><li>Layer: Layer</li></ul>", ent.popupContent["content"])
        self.assertEqual("#FFFFFF", ent.popupContent["color"])
        self.assertTrue(ent.popupContent["linetype"])
        self.assertEqual("Layer - Layer", ent.popupContent["layer"])

    def test_entity_popup_layer_name_bleach(self):
        layer = Layer.objects.get(name="Layer")
        layer.name = "<scrip>alert('hello')</script>"
        layer.save()
        ent = Entity.objects.get(layer=layer)
        self.assertEqual(ent.popupContent["layer"], "Layer - alert('hello')")
        self.assertIn("<li>Layer: alert('hello')</li>", ent.popupContent["content"])

    def test_entity_popup_data(self):
        layer = Layer.objects.get(name="Layer")
        ent = Entity.objects.get(layer=layer)
        EntityData.objects.create(
            entity=ent,
            key="foo",
            value="bar",
        )
        self.assertIn("<li>foo = bar</li>", ent.popupContent["content"])

    def test_entity_popup_data_bleach(self):
        layer = Layer.objects.get(name="Layer")
        ent = Entity.objects.get(layer=layer)
        EntityData.objects.create(
            entity=ent,
            key="foo",
            value="<scrip>alert('hello')</script>",
        )
        self.assertIn("<li>foo = alert('hello')</li>", ent.popupContent["content"])

    def test_entity_popup_data_attributes(self):
        layer = Layer.objects.get(name="Layer")
        layer.is_block = True
        layer.save()
        ent = Entity.objects.get(layer=layer)
        ent.block = layer
        ent.save()
        EntityData.objects.create(
            entity=ent,
            key="foo",
            value="bar",
        )
        self.assertIn("<li>Block: Layer</li>", ent.popupContent["content"])
        self.assertIn("<p>Attributes</p>", ent.popupContent["content"])
        self.assertIn("<li>foo = bar</li>", ent.popupContent["content"])

    def test_room_entity_popup(self):
        draw = Drawing.objects.get(title="Referenced")
        one = Layer.objects.get(drawing=draw, name="one")
        ent_list = Entity.objects.filter(layer=one).values_list("id", flat=True)
        ent_data = EntityData.objects.get(value="Room", entity_id__in=ent_list)
        ent = Entity.objects.get(id=ent_data.entity.id)
        self.assertEqual(ent.popupContent["color"], one.color_field)
        self.assertEqual(ent.popupContent["layer"], f"Layer - {one.name}")
        self.assertIn(f"<li>Layer: {one.name}</li>", ent.popupContent["content"])
        self.assertIn(f"<p>ID = {ent.id}</p>", ent.popupContent["content"])
        self.assertIn(f"<li>Name = {ent_data.value}</li>", ent.popupContent["content"])
        ent_data = EntityData.objects.get(key="Surface", entity=ent)
        self.assertIn(
            f"<li>Surface = {ent_data.value}</li>", ent.popupContent["content"]
        )
        ent_data = EntityData.objects.get(key="Height", entity=ent)
        self.assertIn(
            f"<li>Height = {ent_data.value}</li>", ent.popupContent["content"]
        )
        ent_data = EntityData.objects.get(key="Perimeter", entity=ent)
        self.assertIn(
            f"<li>Perimeter = {ent_data.value}</li>", ent.popupContent["content"]
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
        self.assertEqual(len(response.context["unreferenced"]), 2)

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
        self.assertEqual(len(response.context["lines"]), 6)
        self.assertEqual(len(response.context["layer_list"]), 4)

    @skip("problems with admin views")
    def test_drawing_add_parent_in_admin(self):
        self.client.login(username="boss", password="p4s5w0r6")
        notref = Drawing.objects.get(title="Unreferenced")
        yesref = Drawing.objects.get(title="Referenced")
        response = self.client.post(
            f"/admin/djeocad/drawing/{notref.id}/change/",
            {
                "title": notref.title,
                "parent": yesref.id,
                "dxf": "",
                "image": "",
                "geom": "",
                "designx": 0,
                "designy": 0,
                "rotation": 0,
                "related_layers-TOTAL_FORMS": 0,
                "related_layers-MIN_NUM_FORMS": 0,
                "related_layers-MAX_NUM_FORMS": 1000,
                "related_layers-__prefix__-id": "",
                "related_layers-__prefix__-drawing": notref.id,
                "related_layers-__prefix__-name": "",
                "related_layers-__prefix__-color_field": "#FFFFFF",
                "related_layers-__prefix__-linetype": "on",
            },
            # follow=True,
        )
        self.assertEqual(response.status_code, 302)

    @skip("problems with admin views")
    def test_drawing_add_geom_in_admin(self):
        self.client.login(username="boss", password="p4s5w0r6")
        notref = Drawing.objects.get(title="Unreferenced")
        response = self.client.post(
            f"/admin/djeocad/drawing/{notref.id}/change/",
            {
                "title": notref.title,
                "parent": "",
                "dxf": "",
                "image": "",
                "geom": {"type": "Point", "coordinates": [12.0, 42.0]},
                "designx": 0,
                "designy": 0,
                "rotation": 0,
                "related_layers-TOTAL_FORMS": 0,
                "related_layers-MIN_NUM_FORMS": 0,
                "related_layers-MAX_NUM_FORMS": 1000,
                "related_layers-__prefix__-id": "",
                "related_layers-__prefix__-drawing": notref.id,
                "related_layers-__prefix__-name": "",
                "related_layers-__prefix__-color_field": "#FFFFFF",
                "related_layers-__prefix__-linetype": "on",
                "_save": "Save",
            },
            # follow=True,
        )
        self.assertEqual(response.status_code, 302)

    @skip("problems with admin views")
    def test_drawing_change_dxf_in_admin(self):
        dxf_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/yesgeo.dxf")
        with open(dxf_path, "rb") as f:
            content = f.read()
        self.client.login(username="boss", password="p4s5w0r6")
        notref = Drawing.objects.get(title="Unreferenced")
        response = self.client.post(
            f"/admin/djeocad/drawing/{notref.id}/change/",
            {
                "title": notref.title,
                "parent": "",
                "dxf": SimpleUploadedFile("yesgeo.dxf", content, "image/x-dxf"),
                "image": "",
                "geom": "",
                "designx": 0,
                "designy": 0,
                "rotation": 0,
                "related_layers-TOTAL_FORMS": 0,
                "related_layers-MIN_NUM_FORMS": 0,
                "related_layers-MAX_NUM_FORMS": 1000,
                "related_layers-__prefix__-id": "",
                "related_layers-__prefix__-drawing": notref.id,
                "related_layers-__prefix__-name": "",
                "related_layers-__prefix__-color_field": "#FFFFFF",
                "related_layers-__prefix__-linetype": "on",
            },
            # follow=True,
        )
        self.assertEqual(response.status_code, 302)

    @skip("problems with admin views")
    def test_drawing_change_other_stuff_in_admin(self):
        self.client.login(username="boss", password="p4s5w0r6")
        notref = Drawing.objects.get(title="Unreferenced")
        response = self.client.post(
            f"/admin/djeocad/drawing/{notref.id}/change/",
            {
                "title": notref.title,
                "parent": "",
                "dxf": "",
                "image": "",
                "geom": "",
                "designx": 10,
                "designy": 10,
                "rotation": 30,
                "related_layers-TOTAL_FORMS": 0,
                "related_layers-MIN_NUM_FORMS": 0,
                "related_layers-MAX_NUM_FORMS": 1000,
                "related_layers-__prefix__-id": "",
                "related_layers-__prefix__-drawing": notref.id,
                "related_layers-__prefix__-name": "",
                "related_layers-__prefix__-color_field": "#FFFFFF",
                "related_layers-__prefix__-linetype": "on",
            },
            # follow=True,
        )
        self.assertEqual(response.status_code, 302)

    def test_drawing_get_geodata_from_dxf_false(self):
        # we want to make sure that nogeo.dxf has not been polluted
        dxf_path = Path(settings.BASE_DIR).joinpath("tests/static/tests/nogeo.dxf")
        with open(dxf_path, "rb") as f:
            content = f.read()
        draw = Drawing.objects.get(title="Unreferenced")
        draw.dxf = SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf")
        draw.save()
        doc = draw.get_geodata_from_dxf()
        self.assertFalse(doc)

    def test_drawing_change_view_in_admin(self):
        self.client.login(username="boss", password="p4s5w0r6")
        notref = Drawing.objects.get(title="Unreferenced")
        response = self.client.get(f"/admin/djeocad/drawing/{notref.id}/change/")
        self.assertEqual(response.status_code, 200)

    def test_add_block_insertion_view(self):
        # test unlogged user
        draw = Drawing.objects.get(title="Referenced")
        response = self.client.get(
            reverse("djeocad:insertion_create", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 302)
        # test logged user
        self.client.login(username="boss", password="p4s5w0r6")
        response = self.client.get(
            reverse("djeocad:insertion_create", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)
        # test context
        self.assertIn("form", response.context)
        self.assertIn("lines", response.context)
        self.assertIn("layer_list", response.context)
        self.assertIn("drawing", response.context)
        # test template
        self.assertTemplateUsed(response, "djeocad/entity_create.html")
        # test wrong drawing id
        response = self.client.get(
            reverse("djeocad:insertion_create", kwargs={"pk": 99})
        )
        self.assertEqual(response.status_code, 404)
        layer = Layer.objects.get(drawing=draw, name="0")
        block = Layer.objects.filter(drawing=draw, is_block=True).last()
        # check block name
        self.assertEqual(block.name, "block")
        before = Entity.objects.count()
        response = self.client.post(
            reverse("djeocad:insertion_create", kwargs={"pk": draw.id}),
            {
                "layer": layer.id,
                "block": block.id,
                "rotation": 0,
                "xscale": 1,
                "yscale": 1,
                "lat": 42,
                "long": 12,
            },
            follow=True,
        )
        # check Entity creation
        self.assertEqual(Entity.objects.count() - before, 1)
        ent = Entity.objects.last()
        # check response redirects
        self.assertRedirects(
            response,
            reverse("djeocad:insertion_change", kwargs={"pk": ent.id}),
            status_code=302,
            target_status_code=200,
        )

    def test_change_block_insertion_view(self):
        # test unlogged user
        ent = Entity.objects.exclude(block=None).last()
        response = self.client.get(
            reverse("djeocad:insertion_change", kwargs={"pk": ent.id})
        )
        self.assertEqual(response.status_code, 302)
        # test logged user
        self.client.login(username="boss", password="p4s5w0r6")
        response = self.client.get(
            reverse("djeocad:insertion_change", kwargs={"pk": ent.id})
        )
        self.assertEqual(response.status_code, 200)
        # test context
        self.assertIn("form", response.context)
        self.assertIn("lines", response.context)
        self.assertIn("layer_list", response.context)
        self.assertIn("drawing", response.context)
        self.assertIn("object", response.context)
        self.assertIn("related_data", response.context)
        self.assertIn("data_form", response.context)
        # test template
        self.assertTemplateUsed(response, "djeocad/entity_change.html")
        # test wrong entity id
        response = self.client.get(
            reverse("djeocad:insertion_change", kwargs={"pk": 99})
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.post(
            reverse("djeocad:insertion_change", kwargs={"pk": ent.id}),
            {
                "layer": ent.layer.id,
                "block": ent.block.id,
                "rotation": 0,
                "xscale": 1,
                "yscale": 1,
                "lat": 42,
                "long": 12,
            },
            follow=True,
        )
        # check response redirects
        self.assertRedirects(
            response,
            reverse("djeocad:drawing_detail", kwargs={"pk": ent.layer.drawing.id}),
            status_code=302,
            target_status_code=200,
        )

    def test_entity_create_form(self):
        ent = Entity.objects.exclude(block=None).last()
        form = EntityCreateForm(
            data={
                "layer": ent.layer.id,
                "block": ent.block.id,
                "rotation": 0,
                "xscale": 1,
                "yscale": 1,
                "lat": 142,
                "long": 212,
            }
        )
        self.assertEqual(form.errors["lat"], ["Invalid value"])
        self.assertEqual(form.errors["long"], ["Invalid value"])

    def test_delete_block_insertion(self):
        # test unlogged user
        ent = Entity.objects.exclude(block=None).last()
        response = self.client.get(
            reverse("djeocad:insertion_delete", kwargs={"pk": ent.id})
        )
        self.assertEqual(response.status_code, 302)
        # test logged user
        self.client.login(username="boss", password="p4s5w0r6")
        response = self.client.get(
            reverse("djeocad:insertion_delete", kwargs={"pk": ent.id}), follow=True
        )
        # check response redirects
        self.assertRedirects(
            response,
            reverse("djeocad:drawing_detail", kwargs={"pk": ent.layer.drawing.id}),
            status_code=302,
            target_status_code=200,
        )
        # check entity deleted
        self.assertFalse(Entity.objects.filter(id=ent.id).exists())
        # test wrong entity id
        response = self.client.get(
            reverse("djeocad:insertion_delete", kwargs={"pk": 99})
        )
        self.assertEqual(response.status_code, 404)

    def test_create_entity_data(self):
        # test unlogged user
        ent = Entity.objects.exclude(block=None).last()
        response = self.client.get(
            reverse("djeocad:data_create", kwargs={"pk": ent.id})
        )
        self.assertEqual(response.status_code, 302)
        self.client.login(username="boss", password="p4s5w0r6")
        # test logged user without htmx headers
        response = self.client.post(
            reverse("djeocad:data_create", kwargs={"pk": ent.id}),
            {"key": "Foo", "value": "Bar"},
        )
        self.assertEqual(response.status_code, 404)
        # test logged user with htmx headers
        response = self.client.post(
            reverse("djeocad:data_create", kwargs={"pk": ent.id}),
            {"key": "Foobinabi", "value": "Bar"},
            headers={"Hx-Request": "true"},
            follow=True,
        )
        # check response redirects
        self.assertRedirects(
            response,
            reverse("djeocad:data_list", kwargs={"pk": ent.id}),
            status_code=302,
            target_status_code=200,
        )
        # check entity data creation
        self.assertTrue(EntityData.objects.filter(entity=ent, key="Foobinabi").exists())
        # test wrong entity id
        response = self.client.post(
            reverse("djeocad:data_create", kwargs={"pk": 99}),
            {"key": "Foobinabi", "value": "Bar"},
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_entity_data(self):
        ent = Entity.objects.exclude(block=None).last()
        ent_data = EntityData.objects.create(
            entity=ent,
            key="Foodelenda",
            value="Bar",
        )
        # test no permissions
        response = self.client.get(
            reverse("djeocad:data_delete", kwargs={"pk": ent_data.id}),
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 302)
        self.client.login(username="boss", password="p4s5w0r6")
        # test wrong entity id
        response = self.client.get(
            reverse("djeocad:data_delete", kwargs={"pk": 99}),
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 404)
        # test no headers
        response = self.client.get(
            reverse("djeocad:data_delete", kwargs={"pk": ent_data.id}),
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.get(
            reverse("djeocad:data_delete", kwargs={"pk": ent_data.id}),
            headers={"Hx-Request": "true"},
            follow=True,
        )
        # check response redirects
        self.assertRedirects(
            response,
            reverse("djeocad:data_list", kwargs={"pk": ent.id}),
            status_code=302,
            target_status_code=200,
        )
        # check entity data creation
        self.assertFalse(
            EntityData.objects.filter(entity=ent, key="Foodelenda").exists()
        )

    def test_list_entity_data(self):
        ent = Entity.objects.exclude(block=None).last()
        EntityData.objects.create(
            entity=ent,
            key="Foolist",
            value="Bar",
        )
        response = self.client.get(
            reverse("djeocad:data_list", kwargs={"pk": ent.id}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "djeocad/htmx/entity_data_list.html")
        self.assertTrue("object" in response.context)
        self.assertTrue("data_form" in response.context)
        self.assertTrue("related_data" in response.context)
        self.assertEqual(response.context["related_data"].count(), 1)
        # test wrong entity
        response = self.client.get(
            reverse("djeocad:data_list", kwargs={"pk": 99}),
        )
        self.assertEqual(response.status_code, 404)

    def test_layer_constraints(self):
        draw = Drawing.objects.get(title="Referenced")
        layer = Layer(drawing=draw, name="LLayyerr")
        layer.save()
        self.assertEqual(layer.name, "LLayyerr")
        layer2 = Layer(drawing=draw, name="Layer")
        layer2.save()
        self.assertNotEqual(layer2.name, "Layer")
