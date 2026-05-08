"""ASGI config for LearnUp Backend."""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from core.ws_middleware import CookieJWTAuthMiddleware
from apps.community import routing as community_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": CookieJWTAuthMiddleware(
        URLRouter(
            community_routing.websocket_urlpatterns
        )
    ),
})
