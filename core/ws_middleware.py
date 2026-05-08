"""
WebSocket JWT Authentication Middleware
=======================================
Reads JWT from HTTP-only cookies and authenticates the user for WebSocket connections.
"""
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from apps.accounts.models import User
from channels.db import database_sync_to_async
from django.http import parse_cookie

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class CookieJWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope.get('headers', []))
        cookie_header = headers.get(b'cookie', b'').decode()
        cookies = parse_cookie(cookie_header)
        
        cookie_name = getattr(settings, "SIMPLE_JWT", {}).get("AUTH_COOKIE", "access_token")
        token = cookies.get(cookie_name)
        
        if token:
            try:
                # Validates the token and raises an error if invalid
                validated_token = UntypedToken(token)
                user_id = validated_token.get("user_id")
                scope['user'] = await get_user(user_id)
            except (InvalidToken, TokenError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)
