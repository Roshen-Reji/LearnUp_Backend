"""Placements Views."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
import json

from core.permissions import IsModerator
from .models import Placement
from .serializers import PlacementSerializer, PlacementCreateSerializer
from . import services


class PlacementListCreateView(APIView):
    """GET/POST /api/v1/placements/"""
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsModerator()]
        return [AllowAny()]

    def get(self, request):
        # Allow basic filtering by batch using the URL query
        batch = request.query_params.get("batch")
        qs = Placement.objects.all()
        
        if batch and batch != "All":
            qs = qs.filter(batch__icontains=batch)
            
        serializer = PlacementSerializer(qs, many=True)
        return Response({"success": True, "data": serializer.data})

    def post(self, request):
        """Manual placement log by moderator."""
        serializer = PlacementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        placement = services.log_custom_placement(request.user.name, request.user.id, serializer.validated_data)
        return Response(
            {"success": True, "data": PlacementSerializer(placement).data},
            status=status.HTTP_201_CREATED
        )


class PlacementDetailView(APIView):
    """DELETE /api/v1/placements/<id>/"""
    permission_classes = [IsAuthenticated, IsModerator]

    def delete(self, request, pk):
        try:
            placement = Placement.objects.get(pk=pk)
            placement.delete()
            return Response({"success": True})
        except Placement.DoesNotExist:
            return Response({"error": "Not found"}, status=404)


class PlacementSyncView(APIView):
    """
    POST /api/v1/placements/sync/
    Special endpoint meant to be called by external Python scraper bots.
    Wipes old records and bulk inserts new ones.
    Requires moderator auth or a special secret key (in a real production app).
    """
    permission_classes = [IsAuthenticated, IsModerator]

    def post(self, request):
        placements_data = request.data.get("placements", [])
        if not isinstance(placements_data, list):
            return Response({"error": "Expected a list of placements"}, status=400)
            
        count = services.clear_and_sync_placements(placements_data)
        return Response({"success": True, "inserted": count})
