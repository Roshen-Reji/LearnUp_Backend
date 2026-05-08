from django.urls import path
from .views import QuestionListView, QuestionCreateView, QuestionDetailView, AnswerView, GenerateDailyView

urlpatterns = [
    path("", QuestionListView.as_view(), name="aptitude-list"),
    path("generate-daily/", GenerateDailyView.as_view(), name="aptitude-generate-daily"),
    path("create/", QuestionCreateView.as_view(), name="aptitude-create"),
    path("answer/", AnswerView.as_view(), name="aptitude-answer"),
    path("<uuid:pk>/", QuestionDetailView.as_view(), name="aptitude-detail"),
]
