"""Aptitude Views."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.permissions import IsModerator
from .models import Question, QuestionAttempt, QuestionCorrect
from .serializers import QuestionSerializer, QuestionStudentSerializer, QuestionCreateSerializer, AnswerSerializer
from . import services


class QuestionListView(APIView):
    """GET /api/v1/aptitude/ — Fetch questions for the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get("category", "coding")
        mode = request.query_params.get("mode", "qotd")
        is_high_iq = request.query_params.get("is_high_iq") == "true"
        pending = request.query_params.get("pending") == "true"
        all_approved = request.query_params.get("all") == "true"

        # Admin views
        if all_approved:
            if not request.user.is_moderator:
                return Response({"error": "Unauthorized"}, status=403)
            filter_cat = request.query_params.get("filter_category")
            qs = Question.objects.filter(approved=True)
            if filter_cat and filter_cat != "all":
                qs = qs.filter(category=filter_cat)
            return Response({"success": True, "data": QuestionSerializer(qs, many=True).data})

        if pending:
            if not request.user.is_moderator:
                return Response({"error": "Unauthorized"}, status=403)
            qs = Question.objects.filter(approved=False)
            return Response({"success": True, "data": QuestionSerializer(qs, many=True).data})

        # Sprint eligibility check
        if mode == "sprint":
            action = request.query_params.get("action")
            eligibility = services.check_sprint_eligibility(request.user)

            if eligibility["status"] == "locked":
                return Response({"success": True, "data": eligibility})

            if eligibility["status"] == "active" or action == "start":
                if action == "start":
                    services.start_sprint(request.user)
                questions = services.get_questions_for_user(request.user, category, "sprint", is_high_iq)
                serialized = self._serialize_for_student(questions, request.user)
                return Response({
                    "success": True,
                    "data": {
                        "status": "active",
                        "remaining_seconds": eligibility.get("remaining_seconds", 300),
                        "questions": serialized,
                    },
                })

            return Response({"success": True, "data": eligibility})

        # Standard fetch
        questions = services.get_questions_for_user(request.user, category, mode, is_high_iq)
        serialized = self._serialize_for_student(questions, request.user)
        return Response({"success": True, "data": serialized})

    def _serialize_for_student(self, questions, user):
        """Serialize questions and hide answers for unattempted ones."""
        result = []
        attempted_ids = set(
            QuestionAttempt.objects.filter(user=user).values_list("question_id", flat=True)
        )
        correct_ids = set(
            QuestionCorrect.objects.filter(user=user).values_list("question_id", flat=True)
        )
        for q in questions:
            if q is None:
                continue
            data = QuestionStudentSerializer(q).data
            data["attempted"] = q.pk in attempted_ids
            data["is_correct"] = q.pk in correct_ids
            if data["attempted"]:
                data["correct_index"] = q.correct_index
                data["explanation"] = q.explanation
            result.append(data)
        return result


class QuestionCreateView(APIView):
    """POST /api/v1/aptitude/create/ — Create a question (moderator only)."""
    permission_classes = [IsAuthenticated, IsModerator]

    def post(self, request):
        # Handle AI Generation Request
        if request.data.get("ai_generate"):
            from .ai_services import generate_custom_questions
            data = generate_custom_questions(
                topic=request.data.get("topic", "General Programming"),
                category=request.data.get("category", "coding"),
                count=request.data.get("count", 5),
                is_high_iq=request.data.get("is_high_iq", False),
                target_branch=request.data.get("target_branch", "General"),
                user=request.user
            )
            return Response({"success": True, "message": "5 questions generated.", "data": data}, status=201)

        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save(approved=True)
        return Response(
            {"success": True, "data": QuestionSerializer(question).data},
            status=status.HTTP_201_CREATED,
        )


class GenerateDailyView(APIView):
    """POST /api/v1/aptitude/generate-daily/"""
    permission_classes = [IsAuthenticated, IsModerator]

    def post(self, request):
        from .ai_services import generate_daily_questions
        stats = generate_daily_questions()
        return Response({
            "success": True,
            "generated": stats
        }, status=201)


class QuestionDetailView(APIView):
    """PATCH/DELETE /api/v1/aptitude/<id>/"""
    permission_classes = [IsAuthenticated, IsModerator]

    def patch(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return Response({"error": "Not found"}, status=404)
        serializer = QuestionSerializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    def delete(self, request, pk):
        Question.objects.filter(pk=pk).delete()
        return Response({"success": True, "message": "Question deleted"})


class AnswerView(APIView):
    """POST /api/v1/aptitude/answer/ — Submit an answer."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.answer_question(
            user=request.user,
            question_id=serializer.validated_data["question_id"],
            selected_index=serializer.validated_data["selected_index"],
            mode=serializer.validated_data.get("mode", "qotd"),
        )
        if "error" in result:
            return Response({"success": False, "error": {"message": result["error"]}}, status=404)
        return Response({"success": True, "data": result})
