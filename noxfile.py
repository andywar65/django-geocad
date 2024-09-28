import nox


# 4.2 is LTS end of life April 2026
@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def test420(session):
    session.install(
        "django==4.2.16",
        "django-colorfield",
        "django-geojson",
        "django-leaflet",
        "easy-thumbnails",
        "environs[django]",
        "ezdxf",
        "nh3",
        "psycopg[binary,pool]",
        "pyproj",
        "shapely",
    )
    session.run("./manage/test.py", external=True)


# 5.1 end of life December 2025
@nox.session(python=["3.10", "3.11", "3.12"])
def test510(session):
    session.install(
        "django==5.1.1",
        "django-colorfield",
        "django-geojson",
        "django-leaflet",
        "easy-thumbnails",
        "environs[django]",
        "ezdxf",
        "nh3",
        "psycopg[binary,pool]",
        "pyproj",
        "shapely",
    )
    session.run("./manage/test.py", external=True)
