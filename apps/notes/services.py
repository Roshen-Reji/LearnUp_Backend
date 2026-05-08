"""Notes Business Logic."""

from .models import Note, NoteReader
from django.shortcuts import get_object_or_404
from django.db.models import F
from apps.accounts.services import award_points

def create_note(user, validated_data):
    note = Note.objects.create(
        uploader=user,
        uploader_name=user.name,
        **validated_data
    )
    # Award points for uploading notes
    award_points(user, "note_upload")
    return note

def record_read(user, note_id):
    note = get_object_or_404(Note, id=note_id)
    reader, created = NoteReader.objects.get_or_create(note=note, user=user)
    
    if created:
        # Atomic increment
        Note.objects.filter(id=note_id).update(reader_count=F("reader_count") + 1)
        note.refresh_from_db(fields=['reader_count'])
        
        # Award points at milestones (e.g., every 10 readers)
        if note.reader_count > 0 and note.reader_count % 10 == 0:
            award_points(note.uploader, "note_read_milestone")
            
    return note
