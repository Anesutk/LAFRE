from pathlib import Path
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env in local development only.
# Render injects these as service environment variables.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def unique(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        clean = (item or "").strip().rstrip("/")
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    os.environ.get("SECRET_KEY", "django-insecure-lafre-local-dev-change-on-deploy"),
)

DEBUG = env_bool("DJANGO_DEBUG", "1")

FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()

# Hosts allowed to serve this backend.
DEFAULT_ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
for raw_url in [FRONTEND_BASE_URL]:
    parsed = urlparse(raw_url)
    if parsed.hostname:
        DEFAULT_ALLOWED_HOSTS.append(parsed.hostname)
if RENDER_EXTERNAL_HOSTNAME:
    DEFAULT_ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
# Useful while assigning the final Render URL. You can replace this with the exact host in production.
DEFAULT_ALLOWED_HOSTS.append(".onrender.com")

if DEBUG:
    ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ",".join(DEFAULT_ALLOWED_HOSTS + ["*"]))
else:
    ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ",".join(DEFAULT_ALLOWED_HOSTS))


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",

    "accounts",
    "students",
    "civilian",
    "citizens",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "students.middleware.SessionIdMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "backend.urls"

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

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"


# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
# Render provides PostgreSQL through DATABASE_URL. Local development now also
# defaults to PostgreSQL via POSTGRES_* variables. SQLite is intentionally not
# the default anymore; set LAFRE_ALLOW_SQLITE=1 only for emergency offline tests.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=int(os.environ.get("DB_CONN_MAX_AGE", "600")),
            ssl_require=env_bool("DATABASE_SSL_REQUIRE", "1" if not DEBUG else "0"),
        )
    }
elif env_bool("LAFRE_ALLOW_SQLITE", "0"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "lafre_dev"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "600")),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Africa/Harare")
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
_render_disk = os.environ.get("RENDER_DISK_PATH", "").strip()
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT") or ((_render_disk and f"{_render_disk.rstrip('/')}/media") or (BASE_DIR / "media")))

# Django 5/6 requires both a default file storage backend and a staticfiles backend
# whenever STORAGES is defined. FileField/ImageField uses the "default" alias
# for generated PDFs and uploaded evidence.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Keep admin pages usable if a deployment temporarily lacks the generated manifest.
WHITENOISE_MANIFEST_STRICT = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "EXCEPTION_HANDLER": "backend.api_exception_handler.lafre_exception_handler",
}


# -----------------------------------------------------------------------------
# CORS / CSRF
# -----------------------------------------------------------------------------
def origins_from_urls(urls: list[str]) -> list[str]:
    origins = []
    for raw_url in urls:
        parsed = urlparse((raw_url or "").strip())
        if parsed.scheme and parsed.netloc:
            origins.append(f"{parsed.scheme}://{parsed.netloc}")
    return origins


_default_origins = unique(origins_from_urls([
    FRONTEND_BASE_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]))
if RENDER_EXTERNAL_HOSTNAME:
    _default_origins.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", "1" if DEBUG else "0")
CORS_ALLOW_CREDENTIALS = True

# django-cors-headers' default allow-list does NOT include our custom X-Session-ID header
# (used to track guest chats before login), so the browser's CORS preflight was rejecting it
# even though CORS_ALLOWED_ORIGINS itself was correct. Explicitly extend the default list
# rather than replacing it, so nothing else (Authorization, Content-Type, etc.) breaks.
from corsheaders.defaults import default_headers as _cors_default_headers  # noqa: E402

CORS_ALLOW_HEADERS = list(_cors_default_headers) + ["x-session-id"]

if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = unique(env_list("CORS_ALLOWED_ORIGINS", ",".join(_default_origins)))

CSRF_TRUSTED_ORIGINS = unique(env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    ",".join(_default_origins + ["http://localhost:8000", "http://127.0.0.1:8000"]),
))


# Security settings for production.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", "0")
    X_FRAME_OPTIONS = "DENY"
    SECURE_CONTENT_TYPE_NOSNIFF = True
    REFERRER_POLICY = "same-origin"


# -----------------------------------------------------------------------------
# AWS / Bedrock / Knowledge Base
# -----------------------------------------------------------------------------
AWS_REGION = os.environ.get(
    "AWS_REGION",
    os.environ.get("BEDROCK_REGION", "us-east-1"),
)

AWS_KB_ID = os.environ.get(
    "AWS_KB_ID",
    os.environ.get(
        "BEDROCK_KB_ID",
        os.environ.get("BEDROCK_KNOWLEDGE_BASE_ID", os.environ.get("AWS_BEDROCK_KB_ID", "")),
    ),
)

AWS_BEDROCK_MODEL_ARN = os.environ.get(
    "AWS_BEDROCK_MODEL_ARN",
    os.environ.get("AWS_BEDROCK_MODEL_ID", ""),
)

# Optional separate model IDs used by the student answer generator.
BEDROCK_FAST_MODEL_ID = os.environ.get("BEDROCK_FAST_MODEL_ID", "")
BEDROCK_SMART_MODEL_ID = os.environ.get("BEDROCK_SMART_MODEL_ID", "")

AWS_PRESIGNED_URL_EXPIRY_SECONDS = int(os.environ.get("AWS_PRESIGNED_URL_EXPIRY_SECONDS", "900"))


# Email / frontend links
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@lafre.local")
