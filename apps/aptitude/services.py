"""Aptitude Business Logic."""

import logging
from django.utils import timezone
from django.db.models import Q
from .models import Question, QuestionAttempt, QuestionCorrect
from apps.accounts.services import award_points

logger = logging.getLogger("apps.aptitude")


def get_questions_for_user(user, category, mode, is_high_iq=False):
    """Fetch eligible questions for a user based on mode and category."""
    attempted_ids = QuestionAttempt.objects.filter(user=user).values_list("question_id", flat=True)

    base_qs = Question.objects.filter(
        category=category,
        approved=True,
        is_high_iq=is_high_iq,
    ).exclude(id__in=attempted_ids)

    if mode == "qotd":
        today = timezone.now().date()
        qotd = base_qs.filter(is_qotd=True, qotd_date=today).first()
        if not qotd:
            qotd = base_qs.order_by("qotd_date", "created_at").first()
            if qotd:
                qotd.is_qotd = True
                qotd.qotd_date = today
                qotd.save(update_fields=["is_qotd", "qotd_date"])
        return [qotd] if qotd else []

    elif mode == "sprint":
        return list(base_qs.order_by("?")[:100])

    elif mode == "browse":
        return list(base_qs.order_by("-created_at"))

    return []


def check_sprint_eligibility(user):
    """Check if the user can start a sprint (weekly cooldown)."""
    from datetime import timedelta
    ONE_WEEK = timedelta(days=7)
    FIVE_MINS = timedelta(minutes=5)
    now = timezone.now()

    if not user.last_sprint_start:
        return {"status": "ready"}

    elapsed = now - user.last_sprint_start
    if elapsed < FIVE_MINS:
        remaining = int((FIVE_MINS - elapsed).total_seconds())
        return {"status": "active", "remaining_seconds": remaining}
    elif elapsed < ONE_WEEK:
        return {"status": "locked", "next_available": (user.last_sprint_start + ONE_WEEK).isoformat()}
    return {"status": "ready"}


def start_sprint(user):
    """Mark sprint as started."""
    user.last_sprint_start = timezone.now()
    user.save(update_fields=["last_sprint_start"])


def answer_question(user, question_id, selected_index, mode="qotd"):
    """Process a user's answer to a question. Returns result dict."""
    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        return {"error": "Question not found"}

    already_attempted = QuestionAttempt.objects.filter(question=question, user=user).exists()

    if already_attempted:
        return {
            "correct": question.correct_index == selected_index,
            "correct_index": question.correct_index,
            "explanation": question.explanation,
            "already_attempted": True,
        }

    # Record attempt
    QuestionAttempt.objects.create(question=question, user=user)
    correct = question.correct_index == selected_index

    if correct:
        QuestionCorrect.objects.create(question=question, user=user)
        event = {"qotd": "qotd_correct", "sprint": "sprint_complete"}.get(mode, "quiz_correct")
        award_points(user, event, {"question_id": str(question_id)})

    return {
        "correct": correct,
        "correct_index": question.correct_index,
        "explanation": question.explanation,
        "already_attempted": False,
    }
