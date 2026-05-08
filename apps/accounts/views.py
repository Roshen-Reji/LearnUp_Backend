"""
Accounts Views — Thin Controllers
====================================
Views handle HTTP request/response only. Business logic is in services.py.
"""

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.db.models import Count

from core.permissions import IsModerator
from .models import User
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)
from . import services


# ══════════════════════════════════════════════════════════════════
# Authentication Views
# ══════════════════════════════════════════════════════════════════

class RegisterView(APIView):
    """POST /api/v1/auth/register — Create a new student account."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = services.register_user(
            name=serializer.validated_data["name"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            branch=serializer.validated_data.get("branch", "CSE"),
            year=serializer.validated_data.get("year", 1),
        )

        return Response(
            {
                "success": True,
                "data": UserProfileSerializer(user).data,
                "message": "Registration successful. Please login.",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/v1/auth/login — Authenticate and set JWT cookies."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        # Record activity for login streak
        services.record_activity(user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Build response with user data
        response = Response(
            {
                "success": True,
                "data": UserProfileSerializer(user).data,
            }
        )

        # Set HTTP-only cookies (XSS-proof)
        jwt_settings = settings.SIMPLE_JWT
        response.set_cookie(
            key=jwt_settings.get("AUTH_COOKIE", "access_token"),
            value=access_token,
            httponly=jwt_settings.get("AUTH_COOKIE_HTTP_ONLY", True),
            secure=jwt_settings.get("AUTH_COOKIE_SECURE", False),
            samesite=jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax"),
            path=jwt_settings.get("AUTH_COOKIE_PATH", "/"),
            max_age=int(jwt_settings["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        )
        response.set_cookie(
            key=jwt_settings.get("AUTH_COOKIE_REFRESH", "refresh_token"),
            value=refresh_token,
            httponly=True,
            secure=jwt_settings.get("AUTH_COOKIE_SECURE", False),
            samesite=jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax"),
            path="/api/v1/auth/",  # Only sent to auth endpoints
            max_age=int(jwt_settings["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        )

        return response


class LogoutView(APIView):
    """POST /api/v1/auth/logout — Blacklist refresh token & clear cookies."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Blacklist the refresh token
        refresh_cookie = request.COOKIES.get(
            settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token")
        )
        if refresh_cookie:
            try:
                token = RefreshToken(refresh_cookie)
                token.blacklist()
            except Exception:
                pass  # Token was already blacklisted or invalid

        response = Response({"success": True, "message": "Logged out."})

        # Clear cookies
        response.delete_cookie(settings.SIMPLE_JWT.get("AUTH_COOKIE", "access_token"))
        response.delete_cookie(
            settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token"),
            path="/api/v1/auth/",
        )

        return response


class RefreshTokenView(APIView):
    """POST /api/v1/auth/refresh — Rotate the access token using the refresh cookie."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_cookie = request.COOKIES.get(
            settings.SIMPLE_JWT.get("AUTH_COOKIE_REFRESH", "refresh_token")
        )
        if not refresh_cookie:
            return Response(
                {"success": False, "error": {"message": "No refresh token."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_cookie)
            new_access = str(refresh.access_token)

            # Rotate refresh token
            refresh.blacklist()
            new_refresh = RefreshToken.for_user(
                User.objects.get(pk=refresh.payload.get("user_id"))
            )

            response = Response({"success": True})

            jwt_settings = settings.SIMPLE_JWT
            response.set_cookie(
                key=jwt_settings.get("AUTH_COOKIE", "access_token"),
                value=new_access,
                httponly=True,
                secure=jwt_settings.get("AUTH_COOKIE_SECURE", False),
                samesite=jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax"),
                path="/",
                max_age=int(jwt_settings["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            )
            response.set_cookie(
                key=jwt_settings.get("AUTH_COOKIE_REFRESH", "refresh_token"),
                value=str(new_refresh),
                httponly=True,
                secure=jwt_settings.get("AUTH_COOKIE_SECURE", False),
                samesite=jwt_settings.get("AUTH_COOKIE_SAMESITE", "Lax"),
                path="/api/v1/auth/",
                max_age=int(jwt_settings["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            )
            return response

        except Exception:
            return Response(
                {"success": False, "error": {"message": "Invalid refresh token."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class MeView(APIView):
    """GET /api/v1/auth/me — Get current authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services.check_and_reset_streak(request.user)
        return Response(
            {"success": True, "data": UserProfileSerializer(request.user).data}
        )


# ══════════════════════════════════════════════════════════════════
# User Management Views
# ══════════════════════════════════════════════════════════════════

class UserListView(ListAPIView):
    """GET /api/v1/users/ — List all users (moderator only)."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsModerator]

    def get_queryset(self):
        return User.objects.all().prefetch_related("badges")

    def post(self, request):
        """Create a new user from the moderator panel."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = services.register_user(
            name=serializer.validated_data["name"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            branch=serializer.validated_data.get("branch", "CSE"),
            year=serializer.validated_data.get("year", 1),
        )
        
        # Override role if provided
        if role := request.data.get("role"):
            user.role = role
            user.save(update_fields=["role"])

        return Response(
            {"success": True, "data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET/PATCH/DELETE /api/v1/users/<id>/
    Moderator can view, edit, or delete any user.
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsModerator]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UserUpdateSerializer
        return UserSerializer


class LeaderboardView(APIView):
    """GET /api/v1/users/leaderboard/ — Top 50 students by points."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        leaderboard = services.get_leaderboard()
        return Response({"success": True, "data": leaderboard})


class IEEEVerifyView(APIView):
    """POST /api/v1/users/ieee-verify/ — Submit IEEE card for review."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        card_url = request.data.get("card_url", "").strip()
        if not card_url:
            return Response(
                {"success": False, "error": {"message": "Card URL is required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = services.submit_ieee_card(request.user, card_url)
        return Response({"success": True, "data": result})


class IEEEManualVerifyView(APIView):
    """POST /api/v1/users/ieee-manual-verify/ — Moderator verify/reject."""
    permission_classes = [IsAuthenticated, IsModerator]

    def post(self, request):
        target_user_id = request.data.get("target_user_id")
        action = request.data.get("action", "verify")

        if not target_user_id:
            return Response(
                {"success": False, "error": {"message": "Target user ID required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_user = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": {"message": "User not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = services.verify_ieee_membership(target_user, action)
        return Response({"success": True, "data": result})
