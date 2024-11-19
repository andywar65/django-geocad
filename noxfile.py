import nox


# 4.2 is LTS end of life April 2026
@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def test420(session):
    session.install(
        "django==4.2",
        "django-colorfield",
        "django-geojson",
        "django-leaflet",
        "easy-thumbnails",
        "environs[django]",
        "ezdxf",
        "nh3",
        "pyproj",
        "shapely",
    )
    session.run(
        "./project/manage.py test --settings=project.settings.tests", external=True
    )


# 5.1 end of life December 2025
@nox.session(python=["3.10", "3.11", "3.12"])
def test510(session):
    session.install(
        "django==5.1",
        "django-colorfield",
        "django-geojson",
        "django-leaflet",
        "easy-thumbnails",
        "environs[django]",
        "ezdxf",
        "nh3",
        "pyproj",
        "shapely",
    )
    session.run(
        "./project/manage.py test --settings=project.settings.tests", external=True
    )
