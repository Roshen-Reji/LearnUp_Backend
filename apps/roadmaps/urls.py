from django.urls import path
from .views import (
    RoadmapListCreateView, RoadmapDetailView, RoadmapToggleNodeView, RoadmapApproveView
)

urlpatterns = [
    path("", RoadmapListCreateView.as_view(), name="roadmap-list-create"),
    path("<uuid:pk>/", RoadmapDetailView.as_view(), name="roadmap-detail"),
    path("<uuid:pk>/toggle/", RoadmapToggleNodeView.as_view(), name="roadmap-toggle-node"),
    path("<uuid:pk>/approve/", RoadmapApproveView.as_view(), name="roadmap-approve"),
]
