"""Aptitude Models — Questions, Attempts, Daily Challenges."""

import uuid
from django.db import models
from django.conf import settings


class Question(models.Model):
    class Category(models.TextChoices):
        CODING = "coding", "Coding"
        NUMERICAL = "numerical", "Numerical"
        VERBAL = "verbal", "Verbal"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    options = models.JSONField()  # ["Option A", "Option B", "Option C", "Option D"]
    correct_index = models.IntegerField()
    explanation = models.TextField(blank=True, default="")
    category = models.CharField(max_length=20, choices=Category.choices)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.MEDIUM)

    approved = models.BooleanField(default=False, db_index=True)
    ai_generated = models.BooleanField(default=False)
    is_qotd = models.BooleanField(default=False)
    qotd_date = models.DateField(null=True, blank=True)
    is_high_iq = models.BooleanField(default=False)
    target_branch = models.CharField(max_length=50, default="General")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "approved"]),
        ]

    def __str__(self):
        return f"[{self.category}] {self.text[:60]}..."


class QuestionAttempt(models.Model):
    """Tracks which user attempted which question (1 attempt per question)."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="question_attempts")

    class Meta:
        db_table = "question_attempts"
        unique_together = ("question", "user")


class QuestionCorrect(models.Model):
    """Tracks which user answered which question correctly."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="correct_answers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="correct_questions")

    class Meta:
        db_table = "question_corrects"
        unique_together = ("question", "user")
