"""Community Views."""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from core.permissions import IsModerator, IsOwnerOrModerator
from .models import Post, GlobalChat, Notice, Feedback
from .serializers import (
    PostSerializer, PostCreateSerializer, PostReplySerializer, 
    GlobalChatSerializer, NoticeSerializer, FeedbackSerializer
)
from . import services


class PostListCreateView(APIView):
    """GET/POST /api/v1/community/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = Post.objects.all().prefetch_related("replies", "upvotes")
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response({"success": True, "data": serializer.data})

    def post(self, request):
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = services.create_post(
            user=request.user,
            title=serializer.validated_data["title"],
            body=serializer.validated_data["body"],
            tags=serializer.validated_data.get("tags", [])
        )
        return Response(
            {"success": True, "data": PostSerializer(post, context={'request': request}).data},
            status=status.HTTP_201_CREATED
        )


class PostDetailView(APIView):
    """DELETE /api/v1/community/<id>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)
        
        # Check permissions
        if not (request.user.role == "moderator" or post.author == request.user):
            return Response({"error": "Unauthorized"}, status=403)
            
        services.delete_post(request.user, pk)
        return Response({"success": True, "message": "Post deleted"})


class PostReplyView(APIView):
    """POST /api/v1/community/<id>/reply/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        body = request.data.get("body", "").strip()
        if not body:
            return Response({"error": "Reply body is required"}, status=400)
            
        reply = services.add_reply(request.user, pk, body)
        return Response(
            {"success": True, "data": PostReplySerializer(reply).data},
            status=status.HTTP_201_CREATED
        )


class PostUpvoteView(APIView):
    """POST /api/v1/community/<id>/upvote/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        result = services.toggle_upvote(request.user, pk)
        return Response({"success": True, "data": result})


class GlobalChatListCreateView(APIView):
    """GET/POST /api/v1/community/chat/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get("limit", 50))
        chats = GlobalChat.objects.order_by("-created_at")[:limit]
        # Reverse to show chronological order
        chats = reversed(list(chats))
        return Response({"success": True, "data": GlobalChatSerializer(chats, many=True).data})

    def post(self, request):
        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "Text is required"}, status=400)
            
        msg = services.add_chat_message(request.user, text)
        return Response(
            {"success": True, "data": GlobalChatSerializer(msg).data},
            status=status.HTTP_201_CREATED
        )


class GlobalChatDetailView(APIView):
    """DELETE /api/v1/community/chat/<id>/"""
    permission_classes = [IsAuthenticated, IsModerator]

    def delete(self, request, pk):
        GlobalChat.objects.filter(pk=pk).delete()
        return Response({"success": True})


class NoticeListCreateView(ListCreateAPIView):
    """GET/POST /api/v1/community/notices/"""
    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsModerator()]
        return [AllowAny()]
        
    def perform_create(self, serializer):
        notice = serializer.save(author=self.request.user, author_name=self.request.user.name)
        
        # Broadcast notice via websocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "global_chat",
                {
                    "type": "notification_message",
                    "notice": serializer.data
                }
            )


class FeedbackListCreateView(ListCreateAPIView):
    """GET/POST /api/v1/community/feedback/"""
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated(), IsModerator()]
        return [IsAuthenticated()]
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, user_name=self.request.user.name)


class SettingsView(APIView):
    """GET/PATCH /api/v1/community/settings/"""
    
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated(), IsModerator()]
        return [AllowAny()]
        
    def get(self, request):
        return Response({"success": True, "data": services.get_settings()})
        
    def patch(self, request):
        settings_data = request.data.get("settings", {})
        for k, v in settings_data.items():
            services.update_setting(k, v)
        return Response({"success": True, "data": services.get_settings()})
