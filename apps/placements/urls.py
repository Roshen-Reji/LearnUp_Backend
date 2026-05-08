from django.urls import path
from .views import PlacementListCreateView, PlacementDetailView, PlacementSyncView

urlpatterns = [
    path("", PlacementListCreateView.as_view(), name="placement-list-create"),
    path("sync/", PlacementSyncView.as_view(), name="placement-sync"),
    path("<uuid:pk>/", PlacementDetailView.as_view(), name="placement-detail"),
]
