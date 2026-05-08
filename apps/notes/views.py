"""Notes Views."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Note
from .serializers import NoteSerializer, NoteCreateSerializer
from core.permissions import IsModerator
from . import services


class NoteListCreateView(APIView):
    """GET/POST /api/v1/notes/"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        qs = Note.objects.all()
        
        branch = request.query_params.get("branch")
        if branch and branch != "all":
            qs = qs.filter(branch__iexact=branch)
            
        subject = request.query_params.get("subject")
        if subject:
            qs = qs.filter(subject__icontains=subject)
            
        serializer = NoteSerializer(qs, many=True, context={'request': request})
        # The frontend expects a list directly for notes instead of wrapped in "data" currently, 
        # but let's stick to our standardized unified response unless frontend breaks.
        return Response(serializer.data) # For easy compatibility with `await res.json()` in frontend

    def post(self, request):
        serializer = NoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = services.create_note(request.user, serializer.validated_data)
        return Response(
            NoteSerializer(note, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class NoteDetailView(APIView):
    """PATCH/DELETE /api/v1/notes/<id>/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            note = Note.objects.get(pk=pk)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=404)

        # Moderator editing note metadata
        if request.user.role == "moderator" and any(k in request.data for k in ["title", "subject", "branch", "year"]):
            serializer = NoteCreateSerializer(note, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"success": True, "data": NoteSerializer(note, context={'request': request}).data})
        
        # Default behavior: Mark as read
        services.record_read(request.user, pk)
        return Response({"success": True})

    def delete(self, request, pk):
        try:
            note = Note.objects.get(pk=pk)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=404)
            
        if not (request.user.role == "moderator" or note.uploader == request.user):
            return Response({"error": "Unauthorized"}, status=403)
            
        # Delete file from storage
        if note.file:
            note.file.delete(save=False)
            
        note.delete()
        return Response({"success": True, "message": "Note deleted"})
