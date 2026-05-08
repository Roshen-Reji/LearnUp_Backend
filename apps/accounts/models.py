"""
Accounts Models — Custom User, Badges, Point Events
=====================================================
Custom User model extends Django's AbstractBaseUser for full control.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)  # Uses Argon2 (configured in settings)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "moderator")
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model — UUID primary key, role-based access.
    Replaces Django's default User entirely.
    """

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        MODERATOR = "moderator", "Moderator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    branch = models.CharField(max_length=50, default="CSE")
    year = models.IntegerField(default=1)

    # Gamification
    points = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)
    last_active_date = models.DateTimeField(null=True, blank=True)

    # Premium & Limits
    is_premium = models.BooleanField(default=False)
    roadmap_cap = models.IntegerField(default=3)

    # Aptitude Sprint
    last_sprint_start = models.DateTimeField(null=True, blank=True)

    # IEEE Verification
    ieee_card_url = models.URLField(max_length=500, blank=True, default="")
    ieee_status = models.CharField(
        max_length=20,
        choices=[("none", "None"), ("pending", "Pending"), ("verified", "Verified"), ("failed", "Failed")],
        default="none",
    )

    # GitHub Integration
    github_username = models.CharField(max_length=255, blank=True, default="")
    github_connected = models.BooleanField(default=False)
    github_access_token = models.CharField(max_length=500, blank=True, default="")
    github_points = models.IntegerField(default=0)

    # Django Auth Fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.name} ({self.email})"

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR


class UserBadge(models.Model):
    """Badges earned by users (IEEE Member, Streak Master, etc.)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    badge = models.CharField(max_length=100)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_badges"
        unique_together = ("user", "badge")

    def __str__(self):
        return f"{self.user.name} — {self.badge}"


class PointEvent(models.Model):
    """Audit log of every point awarded — immutable ledger."""

    EVENTS = [
        ("quiz_correct", "Quiz Correct"),
        ("daily_login", "Daily Login"),
        ("streak_bonus", "Streak Bonus"),
        ("note_upload", "Note Upload"),
        ("note_read_milestone", "Note Read Milestone"),
        ("roadmap_node_complete", "Roadmap Node Complete"),
        ("sprint_complete", "Sprint Complete"),
        ("weekly_exam", "Weekly Exam"),
        ("qotd_correct", "QOTD Correct"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="point_events")
    event = models.CharField(max_length=100, choices=EVENTS)
    points = models.IntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "point_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.name} +{self.points} ({self.event})"
