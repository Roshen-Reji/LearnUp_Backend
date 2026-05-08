from django.urls import path
from apps.accounts.views import (
    UserListView,
    UserDetailView,
    LeaderboardView,
    IEEEVerifyView,
    IEEEManualVerifyView,
)

urlpatterns = [
    path("", UserListView.as_view(), name="user-list"),
    path("<uuid:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
    path("ieee-verify/", IEEEVerifyView.as_view(), name="ieee-verify"),
    path("ieee-manual-verify/", IEEEManualVerifyView.as_view(), name="ieee-manual-verify"),
]
