from rest_framework import serializers
from .models import Post, PostReply, GlobalChat, Notice, Feedback, Setting


class PostReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReply
        fields = "__all__"
        read_only_fields = ["id", "post", "author", "author_name", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    upvotes_count = serializers.SerializerMethodField()
    has_upvoted = serializers.SerializerMethodField()
    replies = PostReplySerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            "id", "title", "body", "author_name", "tags",
            "upvotes_count", "has_upvoted", "replies",
            "created_at", "updated_at", "author"
        ]
        read_only_fields = ["id", "author_name", "author", "created_at", "updated_at"]

    def get_upvotes_count(self, obj):
        return obj.upvotes.count()

    def get_has_upvoted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.upvotes.filter(user=request.user).exists()
        return False


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "body", "tags"]


class GlobalChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalChat
        fields = "__all__"
        read_only_fields = ["id", "sender", "sender_name", "created_at"]


class NoticeSerializer(serializers.ModelSerializer):
    imageUrl = serializers.URLField(source='image_url', required=False, allow_blank=True)

    class Meta:
        model = Notice
        fields = ["id", "title", "body", "imageUrl", "image_url", "author", "author_name", "pinned", "form_url", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "author_name", "created_at", "updated_at"]


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = "__all__"
        read_only_fields = ["id", "user", "user_name", "created_at"]


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
