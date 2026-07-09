from __future__ import annotations

import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return int(raw_value)


def env_list(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


SECRET_KEY = os.getenv("WORKFLOW_SECRET_KEY", "change-this-secret-key")
DEBUG = env_bool("WORKFLOW_DEBUG", True)
ALLOWED_HOSTS = env_list("WORKFLOW_ALLOWED_HOSTS", "127.0.0.1,localhost")
APPEND_SLASH = False

WORKFLOW_ACCESS_TOKEN_EXPIRE_MINUTES = env_int("WORKFLOW_ACCESS_TOKEN_EXPIRE_MINUTES", 1440)

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "workflow",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES: list[dict] = []
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("WORKFLOW_MYSQL_DATABASE", "workflow_hub"),
        "USER": os.getenv("WORKFLOW_MYSQL_USER", "workflow_user"),
        "PASSWORD": os.getenv("WORKFLOW_MYSQL_PASSWORD", "workflow_password"),
        "HOST": os.getenv("WORKFLOW_MYSQL_HOST", "127.0.0.1"),
        "PORT": env_int("WORKFLOW_MYSQL_PORT", 3306),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / os.getenv("WORKFLOW_STATIC_ROOT", "staticfiles")
MEDIA_URL = os.getenv("WORKFLOW_MEDIA_URL", "/uploads/")
MEDIA_ROOT = BASE_DIR / os.getenv("WORKFLOW_UPLOAD_DIR", "uploads")
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env_list("WORKFLOW_FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = env_bool("WORKFLOW_CORS_ALLOW_ALL_ORIGINS", DEBUG)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]
CSRF_TRUSTED_ORIGINS = env_list("WORKFLOW_CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env_bool("WORKFLOW_USE_X_FORWARDED_HOST", True)
SECURE_SSL_REDIRECT = env_bool("WORKFLOW_SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("WORKFLOW_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("WORKFLOW_CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = env_int("WORKFLOW_SECURE_HSTS_SECONDS", 31536000 if not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("WORKFLOW_SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("WORKFLOW_SECURE_HSTS_PRELOAD", False)
SECURE_REFERRER_POLICY = os.getenv("WORKFLOW_SECURE_REFERRER_POLICY", "same-origin")
