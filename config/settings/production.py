"""
LearnUp Backend — Production Settings
========================================
Hardened security configuration for cloud deployment.
"""

from .base import *  # noqa: F401,F403

DEBUG = False

# Enforce HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000        # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookie Security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SIMPLE_JWT["AUTH_COOKIE_SECURE"] = True  # noqa: F405
SIMPLE_JWT["AUTH_COOKIE_SAMESITE"] = "None"  # noqa: F405

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# Stricter throttle in production
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "20/minute",
    "user": "100/minute",
}

# Only JSON renderer in production (no browsable API)
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# Production logging — file-based audit trail
LOGGING["handlers"]["file"]["filename"] = "/var/log/learnup/app.log"  # noqa: F405
LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405
