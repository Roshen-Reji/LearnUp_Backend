"""
Role-Based Permissions
=======================
Reusable permission classes for the entire platform.
"""

from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    """Only moderators (admins) can access this endpoint."""
    message = "Moderator privileges required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "moderator"
        )


class IsOwnerOrModerator(BasePermission):
    """Object owner or a moderator can access."""
    message = "You can only access your own resources."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "moderator":
            return True
        # Works for any model that has a `user`, `author`, `uploaded_by`, etc.
        owner_fields = ["user", "author", "uploaded_by", "sender", "created_by"]
        for field in owner_fields:
            owner = getattr(obj, field, None)
            if owner is not None:
                if hasattr(owner, "pk"):
                    return owner.pk == request.user.pk
                return owner == request.user.pk
        return False


class IsStudent(BasePermission):
    """Any authenticated student."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class ReadOnly(BasePermission):
    """Allow unauthenticated read-only access."""
    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")
