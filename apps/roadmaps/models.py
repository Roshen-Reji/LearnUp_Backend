"""Roadmap Models — Personalized learning paths."""

import uuid
from django.db import models
from django.conf import settings

class Roadmap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    topic = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    
    # Store learning nodes sequentially in JSON
    # e.g., [{"id": 1, "title": "Intro", "description": "...", "duration": "2 weeks"}]
    nodes = models.JSONField(default=list)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roadmaps")
    is_global = models.BooleanField(default=False, db_index=True)
    stars = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roadmaps"
        ordering = ["-created_at"]


class UserProgress(models.Model):
    """Tracks a user's progress through a specific roadmap."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="roadmap_progress")
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name="progress_trackers")
    
    # Array of completed Node IDs: [1, 3, 4]
    completed_nodes = models.JSONField(default=list)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_progress"
        unique_together = ("user", "roadmap")
