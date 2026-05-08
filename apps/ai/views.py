"""AI Views."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import ChatRequestSerializer
from . import services


class ChatView(APIView):
    """POST /api/v1/ai/chat/ — Send message to Ollama."""
    
    def get_permissions(self):
        # Allow anyone to chat, but we can rate limit them differently via settings
        return [AllowAny()]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        response_text = services.process_chat_request(
            messages=serializer.validated_data["messages"],
            user=request.user
        )
        
        return Response({
            "success": True,
            "data": {
                "message": response_text
            }
        })
