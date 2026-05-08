from django.urls import path
from .views import GitHubDataView, GitHubAuthView, GitHubCallbackView

urlpatterns = [
    path("", GitHubDataView.as_view(), name="github-data"),
    path("auth/", GitHubAuthView.as_view(), name="github-auth"),
    path("callback/", GitHubCallbackView.as_view(), name="github-callback"),
]
