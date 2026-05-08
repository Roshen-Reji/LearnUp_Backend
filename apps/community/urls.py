from django.urls import path
from .views import (
    PostListCreateView, PostDetailView, PostReplyView, PostUpvoteView,
    GlobalChatListCreateView, GlobalChatDetailView,
    NoticeListCreateView, FeedbackListCreateView, SettingsView
)

urlpatterns = [
    path("", PostListCreateView.as_view(), name="post-list-create"),
    path("<uuid:pk>/", PostDetailView.as_view(), name="post-detail"),
    path("<uuid:pk>/reply/", PostReplyView.as_view(), name="post-reply"),
    path("<uuid:pk>/upvote/", PostUpvoteView.as_view(), name="post-upvote"),
    
    path("chat/", GlobalChatListCreateView.as_view(), name="chat-list-create"),
    path("chat/<uuid:pk>/", GlobalChatDetailView.as_view(), name="chat-detail"),
    
    path("notices/", NoticeListCreateView.as_view(), name="notice-list-create"),
    path("feedback/", FeedbackListCreateView.as_view(), name="feedback-list-create"),
    path("settings/", SettingsView.as_view(), name="settings"),
]
