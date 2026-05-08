"""
Core Views — Health Check, System Status
==========================================
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
import os
import uuid
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser

class FileUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file generated'}, status=400)
            
        ext = file_obj.name.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = default_storage.save(os.path.join('uploads', filename), file_obj)
        file_url = request.build_absolute_uri(default_storage.url(path))
        
        return Response({'success': True, 'fileUrl': file_url})
class HealthCheckView(APIView):
    """
    Health check endpoint for load balancers and monitoring.
    Returns 200 if the service and database are healthy.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # No auth required

    def get(self, request):
        # Check database connectivity
        db_healthy = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_healthy = False

        status_code = 200 if db_healthy else 503
        return Response(
            {
                "status": "healthy" if db_healthy else "degraded",
                "service": "learnup-backend",
                "version": "1.0.0",
                "database": "connected" if db_healthy else "unreachable",
            },
            status=status_code,
        )
