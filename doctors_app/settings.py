"""
Django settings for doctors_app project.
Production-friendly for Render with Channels (Daphne), WhiteNoise, and env-driven config.
"""

from pathlib import Path
import os
import dj_database_url

# -------------------------------------------------------------------
# Base paths
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------------------------------------------
# Security & Debug (read from environment)
# -------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Render injects this automatically; allow it if present
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Optional manual allowlist (comma-separated), e.g. DJANGO_ALLOWED_HOSTS="example.com,api.example.com"
EXTRA_ALLOWED = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
if EXTRA_ALLOWED:
    ALLOWED_HOSTS += [h.strip() for h in EXTRA_ALLOWED.split(",") if h.strip()]

# CSRF trusted origins: read from env (space- or comma-separated) + fallbacks
_csrf_env = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if "," in _csrf_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_env.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_env.split() if o.strip()]

# If Render gives a hostname, add its https origin too
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# (Optional) If you want to hard-allow your current URL now, keep the next line; otherwise you can remove it.
CSRF_TRUSTED_ORIGINS.append("https://curelink3-6.onrender.com")

# If behind a proxy/SSL terminator (Render), tell Django to trust X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -------------------------------------------------------------------
# Applications
# -------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Your apps
    "Users",
    "Hospitals",

    # Channels for ASGI
    "channels",
]

# -------------------------------------------------------------------
# Middleware (WhiteNoise for static files in production)
# -------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serve collected static on Render
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# -------------------------------------------------------------------
# URL / WSGI / ASGI
# -------------------------------------------------------------------
ROOT_URLCONF = "doctors_app.urls"

WSGI_APPLICATION = "doctors_app.wsgi.application"     # still useful for management commands
ASGI_APPLICATION = "doctors_app.asgi.application"     # Daphne will use this

# Channels: start with in-memory layer so you don’t need Redis yet on Render
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
# Later, when you provision Redis on Render:
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {"hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/0")]},
#     }
# }

# -------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -------------------------------------------------------------------
# Database (SQLite by default; switches to DATABASE_URL if set)
# -------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False,
    )
}

# -------------------------------------------------------------------
# Password validation
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------------------------------------------------
# Internationalization
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Static & Media (WhiteNoise)
# -------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic target
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# -------------------------------------------------------------------
# Default PK
# -------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -------------------------------------------------------------------
# Django behavior tweaks
# -------------------------------------------------------------------
APPEND_SLASH = False

# -------------------------------------------------------------------
# Email settings (use env variables; NEVER hardcode real creds)
# -------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

# -------------------------------------------------------------------
# Celery (safe defaults; won’t try localhost Redis unless REDIS_URL is set)
# -------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# If you run Celery Beat separately in production, keep schedules; otherwise you can comment this out.
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    "send-appointment-reminders-every-1-minute": {
        "task": "Hospitals.tasks.send_appointment_reminders",
        "schedule": crontab(minute="*"),  # every 1 minute
    },
}
