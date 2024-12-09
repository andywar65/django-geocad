django-geocad
=============

Django app that imports CAD drawings in Leaflet maps

Overview
--------

Show CAD drawings in interactive web maps, download previously uploaded
files with geo location, download CSV files with extracted data.

Requirements
------------

This app is tested on Django (4.2 to 5.1) and Python (3.9 to 3.12). It
heavily relies on outstanding `ezdxf <https://ezdxf.mozman.at/>`__ for
handling DXF files,
`pyproj <https://pyproj4.github.io/pyproj/stable/>`__ for geographic
projections,
`shapely <https://shapely.readthedocs.io/en/stable/manual.html>`__ for
polygon verification,
`django-leaflet <https://django-leaflet.readthedocs.io/en/latest/>`__
for handling maps,
`django-geojson <https://django-geojson.readthedocs.io/en/latest/>`__
for storing geodata,
`django-colorfield <https://github.com/fabiocaccamo/django-colorfield>`__
for admin color fields. The library relies on
`GDAL <https://gdal.org>`__, which is system specific.

Installation from PyPI
----------------------

Activate your virtual environment and install with:

::

   python -m pip install django-geocad

In your Django project add:

.. code:: python

   INSTALLED_APPS = [
       # ...
       "easy_thumbnails",
       "leaflet",
       "djgeojson",
       "colorfield",
       "djeocad",
   ]

.. code:: python

   # my_project/urls.py
   urlpatterns = [
       # ...
       path('geocad/', include('djeocad.urls', namespace = 'djeocad')),
   ]

You also need to add initial map defaults to ``settings.py`` (these are
the settings for Rome, change them to your location of choice):

.. code:: python

   LEAFLET_CONFIG = {
       "DEFAULT_CENTER": (41.8988, 12.5451),
       "DEFAULT_ZOOM": 10,
       "RESET_VIEW": False
   }

Add two lists to ``my_project/settings.py`` where you can store names of
layers and blocks you don't want to be processed:

.. code:: python

   CAD_LAYER_BLACKLIST = ["name_of_unprocessed_layer", ]
   CAD_BLOCK_BLACKLIST = ["name_of_unprocessed_block", ]

Finally run the following management commands:

::

   python manage.py migrate
   python manage.py collectstatic

Templates
~~~~~~~~~

You also need a ``base.html`` template with following template blocks (a
sample ``base.html`` is provided among package templates).

::

   {% block extra-head %}
   {% end block extra-head %}
   ...
   {% block content %}
   {% endblock content %}

Package comes with several templates in the ``djeocad/templates/``
directory. All templates have no styles. If you want to add your own
styles, copy the templates in a ``my_project/templates/djeocad/``
directory and override them. You will have to set:

.. code:: python

   TEMPLATES = [
       {
           "BACKEND": "django.template.backends.django.DjangoTemplates",
           "DIRS": [BASE_DIR / "my_project/templates"],
           # ...
       },
   ]

.. _moving-from-version-040-to-050-or-later:

Moving from version 0.4.0 to 0.5.0 (or later)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Version ``0.5.0`` has some breaking changes. Once you upgrade run the
following management commands:

::

   python manage.py migrate
   python manage.py collectstatic
   python manage.py populate_block_field

View drawings
-------------

Locally browse to ``127.1.1.0:8000/geocad/``\ to see a
``List of all drawings``, where drawings are just markers on the map.
Click on a marker and follow the link in the popup: you will land on the
``Drawing Detail`` page, with layers displayed on the map. Layers may be
switched on and off.

Create drawings
---------------

To create a ``Drawing`` you must be able to access the ``admin`` with
``GeoCAD Manager`` permissions. You will also need a ``DXF file`` in
ASCII format. ``DXF`` is a drawing exchange format widely used in
``CAD`` applications. Try uploading files with few entities at the
building scale, as the conversion may be inaccurate for small items
(units must be in meters).

.. _geodata--reference-point:

Geodata & Reference Point
~~~~~~~~~~~~~~~~~~~~~~~~~

If ``geodata`` is embedded in the file, the drawing will be imported in
the exact geographical location. If ``geodata`` is unavailable, you will
have to insert it manually: to geolocate the drawing you need to define
a Reference point on the drawing of known Latitude / Longitude.

Design Point
~~~~~~~~~~~~

Mark the point on the map and eventually insert it's coordinates with
respect to the DXF ``World Coordinate System origin (0,0,0)``. A good
position for the ``Reference / Design point`` could be the cornerstone
of a building, or another geographic landmark.

Rotation
~~~~~~~~

Check also the rotation of the drawing with respect to the
``True North``: it is typical to orient the drawings most conveniently
for drafting purposes, unrespectful of True North. Please note that in
CAD counterclockwise rotations are positive, so if you have to rotate
the drawing clockwise to orient it correctly, you will have to enter a
negative angle.

Geodata from Parent
~~~~~~~~~~~~~~~~~~~

Alternatively, you can select a ``Parent`` drawing, that will lend
geolocation to uploaded file. This can be useful when you want to upload
different floors of a single building.

Extraction
~~~~~~~~~~

Press the ``Save`` button. If all goes well the ``DXF file`` will be
extracted and a list of ``Layers`` will be attached to your drawing.
Each layer inherits the ``Name`` and color originally assigned in CAD.
``POINT``, ``ARC``, ``CIRCLE``, ``ELLIPSE``, ``SPLINE``, ``3DFACE``,
``HATCH``, ``LINE`` and ``LWPOLYLINE`` entities are visible on the map
panel, where they inherit layer color. If unnested ``BLOCKS`` are
present in the drawing, they will be extracted and inserted on
respective layer.

Downloading
-----------

In ``Drawing Detail`` view it is possible to download back the
``DXF file``. ``GeoData`` will be associated to the ``DXF``, so if you
work on the file and upload it again, it will be automatically located
on the map.

CSV
~~~

You can also download a ``CSV`` file that contains basic informations of
some entities, notably ``Polylines`` and ``Blocks``. Layer, surface
(only if closed), perimeter, width and thickness are associated to
``Polylines``, while block name, insertion point, scale, rotation and
attribute key/values are associated to ``Blocks``. If a ``TEXT/MTEXT``
is contained in a ``Polyline`` of the same layer, also the text content
will be associated to the entity. This can be helpful if you want to
label rooms.

Adding block instances
----------------------

In ``Drawing Detail`` view it is possible to add ``block instances`` to
the drawing (this works if blocks are actually present in the drawing).
Click on the ``Add insertions`` link, you will be presented with a form
and a map of the drawing. Choose the ``Block`` you want to instantiate
and the ``Layer`` you want to place it on. Choose the
``insertion point`` by clicking on the map. Submit and you will be
redirected to another page where you can modify the insertion or add
``Attributes`` to the block (Key/Value pairs attached to the block
insertion). Submit and you will be redirected to the ``Drawing Detail``
view.

Modify drawings
---------------

Not all changes in the ``Drawing`` will be mirrored into the ``DXF``.
Changes to and deletions of ``Layers`` will not be recorded. New
``Layers`` and new ``Block`` instances will pass into the downloaded
``DXF``. Download it and use your favourite CAD application for further
modifications, then upload it back again (it will be already
geolocated!).

About Geodata
-------------

Geodata can be stored in DXF, but ``ezdxf`` library can't deal with all
kind of Coordinate Reference Systems (CRS). If Geodata is not found in
the file (or if the CRS is not compatible) ``django-geocad`` asks for
user input: the location of a point both on the map and on the drawing
coordinates system, and the rotation with respect to True North. The
``pyproj`` library hands over the best Universal Transverse Mercator CRS
for the location (UTM is compatible with ``ezdxf``). Thanks to UTM,
Reference / Design Point and rotation input, Geodata can be built from
scratch and incorporated into the file.

Tests
-----

Tests with unittest, 96% coverage, missing some special conditions in
DXF extraction. Tested for Django 4.2 and 5.1 and Python 3.9, 3.10,
3.11, 3.12 versions.

Changelog
---------

-  0.6.0: Cannot have two ``Layers`` with the same name in the same
   ``Drawing`` (this is consistent with CAD programs). Newly created
   ``Layers`` and new ``Block`` insertions will be recorded into the
   downloaded ``DXF``.
-  0.5.0: Breaking changes, see installation instructions. Added a
   ``Block`` FK field to ``Entity`` model (previously this information
   was stored in the ``data`` JSONField). Added ``EntityData`` model to
   replace information previously stored in the ``data`` JSONField.
-  0.4.0: First working version
