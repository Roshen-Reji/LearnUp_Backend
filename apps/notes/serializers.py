from rest_framework import serializers
from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = [
            "id", "title", "description", "subject", "branch", "year",
            "file", "file_url", "uploader_name", "reader_count",
            "created_at", "updated_at", "uploader"
        ]
        read_only_fields = ["id", "uploader", "uploader_name", "reader_count", "created_at", "updated_at"]

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        # If we have a file_url stored (e.g. from an external service), favor it.
        # Otherwise, the default 'file' field will return the /media/ URL automatically.
        if repr.get('file_url'):
            repr['fileUrl'] = repr['file_url']
        else:
            repr['fileUrl'] = repr['file']
        
        # Remove original fields to match frontend expectation if needed,
        # but leaving them is fine as long as `fileUrl` exists.
        return repr


class NoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["title", "description", "subject", "branch", "year", "file"]
