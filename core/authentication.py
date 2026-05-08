"""
Custom JWT Authentication — HTTP-Only Cookie Based
====================================================
Reads JWT from HTTP-only cookies instead of the Authorization header.
This is far more secure than localStorage because:
  - Cookies are never accessible to JavaScript (XSS-proof)
  - They are automatically included in every request by the browser
  - SameSite + Secure flags prevent CSRF & man-in-the-middle attacks
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.conf import settings


class CookieJWTAuthentication(JWTAuthentication):
    """
    Attempts to authenticate from:
      1. HTTP-only cookie named 'access_token' (primary)
      2. Authorization: Bearer <token> header (fallback for mobile/Postman)
    """

    def authenticate(self, request):
        # 1. Try cookie first
        cookie_name = getattr(settings, "SIMPLE_JWT", {}).get("AUTH_COOKIE", "access_token")
        raw_token = request.COOKIES.get(cookie_name)

        if raw_token is not None:
            try:
                validated_token = self.get_validated_token(raw_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except (InvalidToken, AuthenticationFailed):
                # Cookie token is invalid/expired — fall through to header
                pass

        # 2. Fall back to Authorization header
        return super().authenticate(request)
