from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'exams', views.ExamViewSet, basename='exam')
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'attempts', views.ExamAttemptViewSet, basename='attempt')
router.register(r'scrape-questions', views.ScrapeQuestionsViewSet, basename='scrape-questions')

urlpatterns = [
    # Includes all viewsets via router.
    path('', include(router.urls)),
]