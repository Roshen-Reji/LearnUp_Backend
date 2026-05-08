"""
Accounts Services — Business Logic Layer
==========================================
ALL business logic lives here, NOT in views.
Views are thin controllers that call these service functions.
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import F, Count
from .models import User, UserBadge, PointEvent

logger = logging.getLogger("apps.accounts")

# ──────────────────────────────────────────────────────────────────
# Points System
# ──────────────────────────────────────────────────────────────────
POINT_VALUES = {
    "quiz_correct": 10,
    "daily_login": 5,
    "streak_bonus": 15,
    "note_upload": 20,
    "note_read_milestone": 10,
    "roadmap_node_complete": 25,
    "sprint_complete": 30,
    "weekly_exam": 50,
    "qotd_correct": 15,
}


def award_points(user: User, event: str, metadata: dict = None) -> int:
    """
    Award points to a user and record the event in the immutable ledger.
    Returns the user's new total points.
    """
    points = POINT_VALUES.get(event, 0)
    if points == 0:
        logger.warning(f"Unknown point event: {event}")
        return user.points

    # Record in audit ledger
    PointEvent.objects.create(
        user=user,
        event=event,
        points=points,
        metadata=metadata or {},
    )

    # Atomic increment (race-condition safe)
    User.objects.filter(pk=user.pk).update(points=F("points") + points)

    # Refresh and return new total
    user.refresh_from_db(fields=["points"])

    # Also record activity for streak
    record_activity(user)

    logger.info(f"Awarded {points} points to {user.email} for {event}")
    return user.points


# ──────────────────────────────────────────────────────────────────
# Activity & Streak Tracking
# ──────────────────────────────────────────────────────────────────

def record_activity(user: User) -> None:
    """
    Update the user's streak based on their last active date.
    Called on any meaningful action (answer question, upload note, etc.)
    """
    now = timezone.now()

    if not user.last_active_date:
        user.streak_days = 1
        user.last_active_date = now
        user.save(update_fields=["streak_days", "last_active_date", "updated_at"])
        return

    last_active = user.last_active_date
    start_of_last = last_active.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    diff_days = (start_of_today - start_of_last).days

    if diff_days == 1:
        # Consecutive day — increment streak
        user.streak_days += 1
    elif diff_days > 1:
        # Missed days — reset streak
        user.streak_days = 1
    # diff_days == 0 → same day, just update timestamp

    user.last_active_date = now
    user.save(update_fields=["streak_days", "last_active_date", "updated_at"])

def check_and_reset_streak(user: User) -> int:
    """
    Check if the user has skipped a day since last_active_date.
    If so, reset streak_days to 0 immediately.
    """
    if not user.last_active_date:
        return 0
        
    now = timezone.now()
    last_active = user.last_active_date
    start_of_last = last_active.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    diff_days = (start_of_today - start_of_last).days
    
    if diff_days > 1:
        if user.streak_days != 0:
            user.streak_days = 0
            user.save(update_fields=["streak_days", "updated_at"])
            
    return user.streak_days



# ──────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────

def register_user(name: str, email: str, password: str, branch: str = "CSE", year: int = 1) -> User:
    """Create a new student account with hashed password."""
    user = User.objects.create_user(
        email=email.lower(),
        name=name,
        password=password,
        branch=branch,
        year=year,
        role="student",
    )
    logger.info(f"New user registered: {email}")
    return user


# ──────────────────────────────────────────────────────────────────
# IEEE Verification
# ──────────────────────────────────────────────────────────────────

def submit_ieee_card(user: User, card_url: str) -> dict:
    """Submit IEEE card for moderator review."""
    if user.ieee_status == "verified":
        return {"status": "already_verified"}

    user.ieee_card_url = card_url
    user.ieee_status = "pending"
    user.save(update_fields=["ieee_card_url", "ieee_status", "updated_at"])
    logger.info(f"IEEE card submitted for review: {user.email}")
    return {"status": "pending"}


def verify_ieee_membership(target_user: User, action: str) -> dict:
    """Moderator approves or rejects IEEE verification."""
    if action == "reject":
        target_user.ieee_status = "failed"
        target_user.save(update_fields=["ieee_status", "updated_at"])
        return {"status": "rejected"}

    target_user.ieee_status = "verified"
    target_user.is_premium = True
    target_user.save(update_fields=["ieee_status", "is_premium", "updated_at"])

    # Award badge
    UserBadge.objects.get_or_create(user=target_user, badge="IEEE Member")

    logger.info(f"IEEE membership verified for {target_user.email}")
    return {"status": "verified"}


# ──────────────────────────────────────────────────────────────────
# Leaderboard
# ──────────────────────────────────────────────────────────────────

def get_leaderboard(limit: int = 50) -> list:
    """Returns the top students by points, enriched with badges."""
    users = (
        User.objects.filter(role="student")
        .order_by("-points")[:limit]
        .values("id", "name", "email", "branch", "year", "points", "streak_days")
    )
    result = []
    for u in users:
        badges = list(
            UserBadge.objects.filter(user_id=u["id"]).values_list("badge", flat=True)
        )
        result.append({**u, "badges": badges})
    return result
