django-geocad
=============

Django app that imports CAD drawings in Leaflet maps

Overview
--------

Show CAD drawings in interactive web maps, download previously uploaded
files with geo location, download CSV files with extracted data.

Requirements
------------

This app is tested on Django 5.1.1 and Python 3.12. It heavily relies on
outstanding `ezdxf <https://ezdxf.mozman.at/>`__ for handling DXF files,
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

   # project/urls.py
   urlpatterns = [
       # ...
       path('geocad/', include('djeocad.urls', namespace = 'djeocad')),
   ]

Migrate and collectstatic. You also need to add initial map defaults to
``settings.py`` (these are the settings for Rome, change them to your
location of choice):

.. code:: python

   LEAFLET_CONFIG = {
       "DEFAULT_CENTER": (41.8988, 12.5451),
       "DEFAULT_ZOOM": 10,
       "RESET_VIEW": False
   }

Add two lists to ``settings.py``, ``CAD_BLOCK_BLACKLIST = []`` and
``CAD_LAYER_BLACKLIST = []``, where you can store names of layers and
blocks you don't want to be processed. You also need a ``base.html``
template with ``{% block extra-head %}`` and ``{% block content %}``
template blocks (an example is provided among the templates).

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
``CAD`` applications. If ``geodata`` is embedded in the file, the
drawing will be imported in the exact geographical location. If
``geodata`` is unavailable, you will have to insert it manually: to
geolocate the drawing you need to define a point on the drawing of known
Latitude / Longitude. Mark the point on the map and insert it's
coordinates with respect to DXF
``World Coordinate System origin (0,0,0)``. A good position for the
``Reference / Design point`` could be the cornerstone of a building, or
another geographic landmark nearby the entities of your drawing. Check
also the rotation of the drawing with respect to the ``True North``: it
is typical to orient the drawings most conveniently for drafting
purposes, unrespectful of True North. Please note that in CAD
counterclockwise rotations are positive, so if you have to rotate the
drawing clockwise to orient it correctly, you will have to enter a
negative angle. Alternatively, you can select a ``Parent`` drawing, that
will lend geolocation to uploaded file. This can be useful when you want
to upload different floors of a single building. Try uploading files
with few entities at the building scale, as the conversion may be
inaccurate for small items (units must be in meters). Press the ``Save``
button. If all goes well the ``DXF file`` will be extracted and a list
of ``Layers`` will be attached to your drawing. Each layer inherits the
``Name`` and color originally assigned in CAD. ``POINT``, ``ARC``,
``CIRCLE``, ``ELLIPSE``, ``SPLINE``, ``3DFACE``, ``HATCH``, ``LINE`` and
``LWPOLYLINE`` entities are visible on the map panel, where they inherit
layer color. If unnested ``BLOCKS`` are present in the drawing, they
will be extracted and inserted on respective layer.

Downloading
-----------

In ``Drawing Detail`` view it is possible to download back the
``DXF file``. ``GeoData`` will be associated to the ``DXF``, so if you
work on the file and upload it again, it will be automatically located
on the map. You can also download a ``CSV`` file that contains basic
informations of some entities, notably ``Polylines`` and ``Blocks``.
Layer, surface (only if closed), perimeter, width and thickness are
associated to ``Polylines``, while block name, insertion point, scale,
rotation and attribute key/values are associated to ``Blocks``. If a
``TEXT/MTEXT`` is contained in a ``Polyline`` of the same layer, also
the text content will be associated to the entity. This can be helpful
if you want to label rooms.

Modify drawings
---------------

You can modify geolocation and appearance of drawings, but the ``DXF``
will not be affected. If you want to modify the file, download it and
use your favourite CAD application, then upload it back again (it will
be already geolocated!).

About Geodata
-------------

Geodata can be stored in DXF, but ``ezdxf`` library can't deal with all
kind of coordinate reference systems (CRS). If Geodata is not found in
the file (or if the CRS is not compatible) ``django-geocad`` asks for
user input: the location of a point both on the map and on the drawing
coordinates system, and the rotation with respect to True North. The
``pyproj`` library hands over the best Universal Transverse Mercator CRS
for the location (UTM is compatible with ``ezdxf``). Thanks to UTM,
Reference / Design Point and rotation input, Geodata can be built from
scratch and incorporated into the file.

Next steps
----------

Tests with unittest, missing some special conditions in DXF extraction.
