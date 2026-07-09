from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "demo-only"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "djust_designer",
]

MIDDLEWARE = ["djust_designer.middleware.DjustDesignerMiddleware"]

ROOT_URLCONF = "demo_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": False,
        "OPTIONS": {
            "loaders": [
                (
                    "djust_designer.instrument.loader.InstrumentedFilesystemLoader",
                    [str(BASE_DIR / "templates")],
                ),
            ],
        },
    },
]

STATIC_URL = "/static/"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
