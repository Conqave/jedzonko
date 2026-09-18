import os
from pathlib import Path

import django_stubs_ext

# Makes Django's generic classes subscriptable at runtime so the annotations
# required by mypy --strict + django-stubs also work when Django imports them.
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    v for v in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if v
]
CSRF_TRUSTED_ORIGINS = [
    v
    for v in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:9000").split(",")
    if v
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "catalog",
    "households",
    "inventory",
    "recipes",
    "shopping",
    "promotions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["MARIADB_DATABASE"],
        "USER": os.environ["MARIADB_USER"],
        "PASSWORD": os.environ["MARIADB_PASSWORD"],
        "HOST": os.environ.get("MARIADB_HOST", "database"),
        "PORT": int(os.environ.get("MARIADB_PORT", "3306")),
        "OPTIONS": {"charset": "utf8mb4"},
        "TEST": {
            "NAME": os.environ.get("DJANGO_TEST_DATABASE", "test_jedzonko"),
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pl-pl"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

PROMOTIONS_HTTP_TIMEOUT_SECONDS = float(os.environ.get("PROMOTIONS_HTTP_TIMEOUT_SECONDS", "10"))
PROMOTIONS_HTTP_USER_AGENT = os.environ.get(
    "PROMOTIONS_HTTP_USER_AGENT", "jedzonko/0.1 (+https://github.com/Conqave/jedzonko)"
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "config.exception_handler.handle_api_exception",
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}
