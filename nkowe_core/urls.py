from django.urls import path

from .views import GuardianDashboardView, LearnerDashboardView, TeacherClassLearnerRecordsView

urlpatterns = [
    path('my-learning-record/', LearnerDashboardView.as_view(), name='my-learning-record'),
    path('guardian/children-records/', GuardianDashboardView.as_view(), name='guardian-children-records'),
    path(
        'classrooms/<int:classroom_id>/learner-records/',
        TeacherClassLearnerRecordsView.as_view(),
        name='classroom-learner-records',
    ),
]
