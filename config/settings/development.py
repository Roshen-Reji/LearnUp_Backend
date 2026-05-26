"""
LearnUp Backend — Development Settings
========================================
Local WAMP / dev machine overrides.
"""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Relax throttling in development
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/minute",
    "user": "5000/minute",
}

# Browsable API for development convenience
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# Cookies: not secure in local dev (HTTP, not HTTPS)
SIMPLE_JWT["AUTH_COOKIE_SECURE"] = False  # noqa: F405

# Show SQL queries in console for debug
LOGGING["loggers"]["django.db.backends"] = {  # noqa: F405
    "handlers": ["console"],
    "level": "WARNING",  # Change to DEBUG to see all SQL queries
    "propagate": False,
}

# CORS: accept all origins during development
CORS_ALLOW_ALL_ORIGINS = True

# Bypass Redis in local development so Windows users don't need a Redis server
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
