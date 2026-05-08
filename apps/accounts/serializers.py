"""
Accounts Serializers — Input Validation & Output Formatting
=============================================================
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserBadge, PointEvent


class RegisterSerializer(serializers.Serializer):
    """Validates registration input — does NOT use ModelSerializer to keep passwords explicit."""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    branch = serializers.CharField(max_length=50, default="CSE")
    year = serializers.IntegerField(default=1, min_value=1, max_value=5)

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value


class LoginSerializer(serializers.Serializer):
    """Validates login credentials."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password", "")
        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Full user representation (excludes sensitive fields)."""
    badges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "name", "role", "branch", "year",
            "points", "streak_days", "is_premium", "roadmap_cap",
            "ieee_card_url", "ieee_status",
            "github_username", "github_connected", "github_points",
            "badges", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_badges(self, obj):
        return list(obj.badges.values_list("badge", flat=True))


class UserProfileSerializer(serializers.ModelSerializer):
    """Slim profile for the current user's session data."""

    class Meta:
        model = User
        fields = [
            "id", "email", "name", "role", "branch", "year",
            "points", "streak_days", "is_premium", "roadmap_cap",
            "ieee_card_url", "ieee_status",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Admin/moderator updating a user's profile."""
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ["name", "email", "branch", "year", "role", "is_premium", "roadmap_cap", "password"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PointEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointEvent
        fields = ["id", "event", "points", "metadata", "created_at"]
