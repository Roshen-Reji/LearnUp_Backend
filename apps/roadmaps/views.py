"""Roadmap Views."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Prefetch

from core.permissions import IsModerator
from .models import Roadmap, UserProgress
from .serializers import RoadmapSerializer, UserProgressSerializer
from . import services


class RoadmapListCreateView(APIView):
    """GET/POST /api/v1/roadmaps/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Roadmap.objects.all()
        # Combine user's roadmaps + global roadmaps
        user_roadmaps = qs.filter(created_by=request.user)
        global_roadmaps = qs.filter(is_global=True).exclude(created_by=request.user)
        
        # Admin looking at all global
        if request.user.role == "moderator" and request.query_params.get("admin") == "true":
            qs = Roadmap.objects.all()
            return Response({"success": True, "data": RoadmapSerializer(qs, many=True).data})

        return Response({
            "success": True,
            "data": {
                "my_roadmaps": RoadmapSerializer(user_roadmaps, many=True).data,
                "global_roadmaps": RoadmapSerializer(global_roadmaps, many=True).data
            }
        })

    def post(self, request):
        # AI generated roadmaps come here
        if request.data.get("ai_propose"):
            skill = request.data.get("skill", "General Skill")
            
            from apps.ai.services import generate_roadmap_json
            generated_nodes = generate_roadmap_json(skill)
            
            if generated_nodes:
                nodes = generated_nodes
            else:
                nodes = [
                    {"day": 1, "topic": f"Introduction to {skill}", "details": "Understand basic concepts.", "completed": False},
                    {"day": 2, "topic": f"Core Syntax & Logic for {skill}", "details": "Learn fundamental logic.", "completed": False},
                    {"day": 3, "topic": f"Advanced {skill} Architecture", "details": "Build your first project.", "completed": False},
                    {"day": 4, "topic": f"Testing & Deployment in {skill}", "details": "Finalize and publish.", "completed": False}
                ]

            roadmap = Roadmap.objects.create(
                title=f"{skill} Masterclass",
                topic=skill,
                description=f"Generated roadmap for learning {skill}.",
                nodes=nodes,
                created_by=request.user,
                is_global=False
            )
            UserProgress.objects.create(user=request.user, roadmap=roadmap)
            return Response({"success": True, "data": RoadmapSerializer(roadmap).data}, status=201)

        # Check roadmap cap limits
        if request.user.roadmaps.count() >= request.user.roadmap_cap and not request.user.is_premium:
            return Response({"error": "Roadmap generation limit reached."}, status=403)
            
        serializer = RoadmapSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        roadmap = serializer.save(created_by=request.user)
        
        # Initialize progress
        UserProgress.objects.create(user=request.user, roadmap=roadmap)
        return Response({"success": True, "data": RoadmapSerializer(roadmap).data}, status=201)


class RoadmapDetailView(APIView):
    """GET/DELETE /api/v1/roadmaps/<id>/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            roadmap = Roadmap.objects.get(pk=pk)
        except Roadmap.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
            
        progress, _ = UserProgress.objects.get_or_create(user=request.user, roadmap=roadmap)
        
        return Response({
            "success": True, 
            "data": {
                "roadmap": RoadmapSerializer(roadmap).data,
                "progress": progress.completed_nodes
            }
        })

    def delete(self, request, pk):
        try:
            roadmap = Roadmap.objects.get(pk=pk)
        except Roadmap.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
            
        if not (request.user.role == "moderator" or roadmap.created_by == request.user):
            return Response({"error": "Unauthorized"}, status=403)
            
        roadmap.delete()
        return Response({"success": True})


class RoadmapToggleNodeView(APIView):
    """PATCH /api/v1/roadmaps/<id>/toggle/"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        node_index = request.data.get("node_index")
        if node_index is None:
            return Response({"error": "node_index required"}, status=400)
            
        result = services.toggle_node(request.user, pk, int(node_index))
        return Response({"success": True, "data": result})


class RoadmapApproveView(APIView):
    """PATCH /api/v1/roadmaps/<id>/approve/"""
    permission_classes = [IsAuthenticated, IsModerator]

    def patch(self, request, pk):
        try:
            roadmap = Roadmap.objects.get(pk=pk)
        except Roadmap.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
            
        approve = request.data.get("approve", True)
        roadmap.is_global = approve
        roadmap.save(update_fields=["is_global"])
        return Response({"success": True})
