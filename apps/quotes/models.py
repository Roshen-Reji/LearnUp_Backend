"""
Motivational Quotes Model
"""
import uuid
from django.db import models
from django.conf import settings


class Quote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField(help_text="The motivational quote text")
    author = models.CharField(max_length=200, blank=True, default="", help_text="Who said it")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_quotes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f'"{self.text[:60]}..." — {self.author or "Unknown"}'
