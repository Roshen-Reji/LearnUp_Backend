from rest_framework import serializers
from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class QuestionStudentSerializer(serializers.ModelSerializer):
    """Hides the answer for unattempted questions."""
    attempted = serializers.BooleanField(default=False, read_only=True)
    is_correct = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = Question
        fields = [
            "id", "text", "options", "category", "difficulty",
            "is_high_iq", "target_branch", "attempted", "is_correct",
        ]


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "text", "options", "correct_index", "explanation",
            "category", "difficulty", "is_high_iq", "target_branch",
        ]


class AnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    selected_index = serializers.IntegerField()
    mode = serializers.CharField(default="qotd")
