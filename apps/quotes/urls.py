from django.urls import path
from .views import QuoteListCreateView, QuoteDetailView, RandomQuoteView

urlpatterns = [
    path("", QuoteListCreateView.as_view(), name="quote-list"),
    path("random/", RandomQuoteView.as_view(), name="quote-random"),
    path("<uuid:pk>/", QuoteDetailView.as_view(), name="quote-detail"),
]
