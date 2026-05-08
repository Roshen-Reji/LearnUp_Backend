from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from core.permissions import IsModerator
from .models import Quote
from .serializers import QuoteSerializer


class QuoteListCreateView(ListCreateAPIView):
    """
    GET  /api/v1/quotes/         — List all quotes (moderator)
    POST /api/v1/quotes/         — Create a quote (moderator)
    """
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsModerator]

    def get_queryset(self):
        return Quote.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuoteDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/v1/quotes/<uuid:pk>/
    """
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated, IsModerator]
    queryset = Quote.objects.all()


class RandomQuoteView(APIView):
    """
    GET /api/v1/quotes/random/ — Get a random active quote for the dashboard.
    Open to all authenticated users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        quote = Quote.objects.filter(is_active=True).order_by("?").first()
        if quote:
            return Response({
                "text": quote.text,
                "author": quote.author,
            })
        # Fallback if no quotes exist
        return Response({
            "text": "The only way to do great work is to love what you do.",
            "author": "Steve Jobs",
        })
