from rest_framework import serializers
from .models import Quote


class QuoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.name", read_only=True, default="System")

    class Meta:
        model = Quote
        fields = ["id", "text", "author", "is_active", "created_by_name", "created_at"]
        read_only_fields = ["id", "created_by_name", "created_at"]
