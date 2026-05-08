from rest_framework import serializers
from .models import Roadmap, UserProgress

class RoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roadmap
        fields = [
            "id", "title", "topic", "description", "nodes",
            "created_by", "is_global", "stars", "created_at"
        ]
        read_only_fields = ["id", "created_by", "created_at"]


class UserProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ["id", "user", "roadmap", "completed_nodes", "last_accessed"]
        read_only_fields = ["id", "user", "roadmap", "last_accessed"]
