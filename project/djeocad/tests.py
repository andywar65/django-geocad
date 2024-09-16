from django.test import TestCase

from .models import Drawing

class GeoCADModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Drawing.objects.create(
            title="Drawing 1",
        )

    def test_drawing_str_method(self):
        draw = Drawing.objects.first()
        self.assertEqual(draw.__str__(), "Drawing 1")
