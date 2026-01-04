from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

from exam_app.suggested_solution.views import (
    SuggestedSolutionViewSet,
    SuggestedSolutionVoteViewSet,
    SolutionCommentViewSet
)

router = DefaultRouter()
router.register(r'exams', views.ExamViewSet, basename='exam')
router.register(r'questions', views.QuestionViewSet, basename='question')
router.register(r'attempts', views.ExamAttemptViewSet, basename='attempt')
router.register(r'scrape-questions', views.ScrapeQuestionsViewSet, basename='scrape-questions')
router.register(r'practice-exam', views.PracticeExamViewSet, basename='practice-exam')
# Register the suggested_solution endpoints
router.register(r'suggested-solutions', SuggestedSolutionViewSet, basename='suggestedsolution')
router.register(r'suggested-solution-votes', SuggestedSolutionVoteViewSet, basename='suggestedsolutionvote')
router.register(r'solution-comments', SolutionCommentViewSet, basename='solutioncomment')
# Do NOT register SchoolNgrAccountsScrapeAPIView with the router (it's an APIView, not a ViewSet).

urlpatterns = [
    path('', include(router.urls)),
    path('scrape-questions2/', views.SchoolNgrAccountsScrapeAPIView.as_view(), name='scrape-questions2'),
]