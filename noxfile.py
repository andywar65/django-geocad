import nox


# 4.2 is LTS end of life April 2026
@nox.session(python=["3.9", "3.10", "3.12"])
def test420(session):
    session.install(
        "django==4.2.16",
        "django-colorfield==0.11.0",
        "django-geojson==4.1.0",
        "django-leaflet==0.30.1",
        "easy-thumbnails==2.10",
        "environs[django]==11.0.0",
        "ezdxf==1.3.3",
        "nh3==0.2.18",
        "psycopg[binary,pool]==3.2.2",
        "pyproj==3.6.1",
        "shapely==2.0.6",
    )
    session.run("./manage/test.py", external=True)


# 5.1 end of life December 2025
@nox.session(python=["3.10", "3.12"])
def test510(session):
    session.install(
        "django==5.1.1",
        "django-colorfield==0.11.0",
        "django-geojson==4.1.0",
        "django-leaflet==0.30.1",
        "easy-thumbnails==2.10",
        "environs[django]==11.0.0",
        "ezdxf==1.3.3",
        "nh3==0.2.18",
        "psycopg[binary,pool]==3.2.2",
        "pyproj==3.6.1",
        "shapely==2.0.6",
    )
    session.run("./manage/test.py", external=True)
