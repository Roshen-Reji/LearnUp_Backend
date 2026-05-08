from rest_framework import serializers
from .models import Placement


class PlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Placement
        fields = "__all__"
        read_only_fields = ["id", "posted_by", "created_at"]


class PlacementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Placement
        fields = ["company", "role", "salary", "batch", "link", "requirements"]
