import os
from pathlib import Path

import django_stubs_ext
from django.core.exceptions import ImproperlyConfigured

django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG_SETTING = os.environ["DJANGO_DEBUG"]
if DEBUG_SETTING not in {"true", "false"}:
    raise ImproperlyConfigured("DJANGO_DEBUG must be 'true' or 'false'.")
DEBUG = DEBUG_SETTING == "true"
ALLOWED_HOSTS = [v for v in os.environ["DJANGO_ALLOWED_HOSTS"].split(",") if v]
CSRF_TRUSTED_ORIGINS = [v for v in os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"].split(",") if v]

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
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
        "HOST": os.environ["MARIADB_HOST"],
        "PORT": int(os.environ["MARIADB_PORT"]),
        "OPTIONS": {"charset": "utf8mb4"},
        "TEST": {
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
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ["DJANGO_MEDIA_ROOT"])

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

PROMOTIONS_HTTP_TIMEOUT_SECONDS = float(os.environ["PROMOTIONS_HTTP_TIMEOUT_SECONDS"])
PROMOTIONS_HTTP_USER_AGENT = os.environ["PROMOTIONS_HTTP_USER_AGENT"]
PROMOTIONS_SEARCH_LEAFLET_LIMIT = int(os.environ["PROMOTIONS_SEARCH_LEAFLET_LIMIT"])
PROMOTIONS_SEARCH_RESULT_LIMIT = int(os.environ["PROMOTIONS_SEARCH_RESULT_LIMIT"])

RECIPE_SOURCE_HTTP_TIMEOUT_SECONDS = float(os.environ["RECIPE_SOURCE_HTTP_TIMEOUT_SECONDS"])
RECIPE_SOURCE_HTTP_USER_AGENT = os.environ["RECIPE_SOURCE_HTTP_USER_AGENT"]
RECIPE_SOURCE_PAGE_SIZE_LIMIT = int(os.environ["RECIPE_SOURCE_PAGE_SIZE_LIMIT"])
RECIPE_SOURCE_SUGGESTION_INGREDIENT_LIMIT = int(
    os.environ["RECIPE_SOURCE_SUGGESTION_INGREDIENT_LIMIT"]
)

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]
OLLAMA_REASONING_EFFORT = os.environ["OLLAMA_REASONING_EFFORT"]
OLLAMA_HTTP_TIMEOUT_SECONDS = float(os.environ["OLLAMA_HTTP_TIMEOUT_SECONDS"])
OLLAMA_MAX_OUTPUT_TOKENS = int(os.environ["OLLAMA_MAX_OUTPUT_TOKENS"])
INGREDIENT_CLASSIFIER_QUESTION_LIMIT = int(os.environ["INGREDIENT_CLASSIFIER_QUESTION_LIMIT"])

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "config.exception_handler.handle_api_exception",
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}
