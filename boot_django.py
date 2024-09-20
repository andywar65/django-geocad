# File sets up the django environment, used by other scripts that need to
# execute in Django land

import sys
from pathlib import Path

import django
from django.conf import settings
from environs import Env

env = Env()
env.read_env()

BASE_DIR = Path(__file__).parent / "src"
sys.path.insert(0, str(BASE_DIR))


def boot_django():
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=True,
        DATABASES={"default": env.dj_db_url("DATABASE_URL")},
        INSTALLED_APPS=(
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "easy_thumbnails",
            "leaflet",
            "djgeojson",
            "colorfield",
            "djeocad",
        ),
        LEAFLET_CONFIG={
            "DEFAULT_CENTER": (41.8988, 12.5451),
            "DEFAULT_ZOOM": 10,
            "RESET_VIEW": False,
        },
        CAD_BLOCK_BLACKLIST=[
            "*Model_Space",
            "DynamicInputDot",
        ],
        CAD_LAYER_BLACKLIST=[
            "Defpoints",
        ],
        TIME_ZONE="UTC",
        USE_TZ=True,
        ROOT_URLCONF="tests.urls",
        STATIC_URL="/static/",
        STATIC_ROOT=env.str("STATIC_ROOT"),
        MEDIA_URL="/media/",
        MEDIA_ROOT=env.str("MEDIA_ROOT"),
    )

    django.setup()
