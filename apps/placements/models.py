"""Placements Models — Scraped Job & Internship data."""

import uuid
from django.db import models
from django.conf import settings

class Placement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=500)
    salary = models.CharField(max_length=255)
    batch = models.CharField(max_length=100)
    link = models.URLField(max_length=1000)
    
    # Store requirements like ["B.Tech", "M.Tech", "60% aggregate"]
    requirements = models.JSONField(default=list, blank=True)
    
    posted_by = models.CharField(max_length=255, default="SystemScraper")
    
    # Optional foreign key to whoever actually posted it (if manual)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "placements"
        ordering = ["-created_at"]
        
    def __str__(self):
        return f"{self.company} - {self.role}"
