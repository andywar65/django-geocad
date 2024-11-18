# File sets up the django environment, used by other scripts that need to
# execute in Django land

import sys
from pathlib import Path

import django
from django.conf import settings
from environs import Env

env = Env()
env.read_env()

BASE_DIR = Path(__file__).parent.parent / "src"
REPO_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))


def boot_django():
    settings.configure(
        BASE_DIR=BASE_DIR,
        SECRET_KEY="django-insecure-@!g#+nmv6464ignk@+mjx(r^+7e0ne6h6!o5y#h@u1d+$38(+9",
        DEBUG=True,
        DATABASES={"default": env.dj_db_url("DATABASE_URL")},
        INSTALLED_APPS=(
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.messages",
            "django.contrib.sessions",
            "easy_thumbnails",
            "leaflet",
            "djgeojson",
            "colorfield",
            "djeocad",
        ),
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [REPO_DIR / "project/project/templates"],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ],
                },
            },
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        LEAFLET_CONFIG={
            "DEFAULT_CENTER": (41.8988, 12.5451),
            "DEFAULT_ZOOM": 10,
            "RESET_VIEW": False,
        },
        CAD_BLOCK_BLACKLIST=[
            "*Model_Space",
            "DynamicInputDot",
            "blacklist",
        ],
        CAD_LAYER_BLACKLIST=[
            "Defpoints",
        ],
        TIME_ZONE="UTC",
        USE_TZ=True,
        ROOT_URLCONF="urls",
        STATIC_URL="/static/",
        STATIC_ROOT=env.str("STATIC_ROOT"),
        MEDIA_URL="/media/",
        MEDIA_ROOT=env.str("MEDIA_ROOT"),
    )

    django.setup()
