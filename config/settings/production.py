from .base import *
import environ
import os

env = environ.Env()

DEBUG = False

DATABASES = {
    'default': env.db('DATABASE_URL')
}

# ── Security ──────────────────────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@example.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ── Logging ───────────────────────────────────────────────────────────────────
_LOG_LEVEL = env('LOG_LEVEL', default='WARNING')
_LOG_DIR = env('LOG_DIR', default='')

_handlers = ['console']
if _LOG_DIR:
    os.makedirs(_LOG_DIR, exist_ok=True)
    _handlers.append('file')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(_LOG_DIR, 'django.log') if _LOG_DIR else '/dev/null',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': _handlers,
            'level': _LOG_LEVEL,
            'propagate': False,
        },
        'django.request': {
            'handlers': _handlers,
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': _handlers,
            'level': _LOG_LEVEL,
            'propagate': False,
        },
    },
}

# ── Sentry (opt-in via SENTRY_DSN env var) ───────────────────────────────────
_SENTRY_DSN = env('SENTRY_DSN', default='')
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1),
            send_default_pii=False,
        )
    except ImportError:
        pass  # sentry-sdk not installed; add it to requirements when ready
