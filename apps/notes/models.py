"""Notes Models — File Sharing."""

import uuid
import os
from django.db import models
from django.conf import settings

def notes_upload_path(instance, filename):
    # e.g., media/notes/<uuid_filename>
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("notes", filename)

class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    subject = models.CharField(max_length=255)
    branch = models.CharField(max_length=50)
    year = models.IntegerField()
    
    file = models.FileField(upload_to=notes_upload_path)
    # Storing URL to maintain compatibility or for external storage
    file_url = models.URLField(max_length=1000, blank=True, default="")
    
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploaded_notes")
    uploader_name = models.CharField(max_length=255)
    
    reader_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notes"
        ordering = ["-created_at"]
        
    def __str__(self):
        return f"{self.title} - {self.subject}"

class NoteReader(models.Model):
    """Tracks unique reads to avoid inflating view counts."""
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="readers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        db_table = "note_readers"
        unique_together = ("note", "user")
