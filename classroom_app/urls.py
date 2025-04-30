from django.urls import path, include
from rest_framework import routers

from classroom_app.classroom.views import ClassroomTermsAndConditionsViewSet
from classroom_app.institution.views import InstitutionViewSet
from classroom_app.assignment.views import AssignmentViewSet
from classroom_app.assignment.views import StudentAssignmentCreateUpdateView
from classroom_app.assignment.views import StudentAssignmentDetailView
from classroom_app.assignment.views import AllStudentAssignmentsView
from classroom_app.definitions.subjects.views import SubjectViewSet
from classroom_app.definitions.insitution_types.views import InstitutionTypeViewSet
from classroom_app.definitions.examination_types.views import ExaminationTypeViewSet
from .views import ClassroomViewSet, ClassroomTutorViewSet, ClassroomStudentViewSet, ClassroomExaminationViewSet, ClassroomAttachmentViewSet

router = routers.DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classrooms')
router.register(r'institution', InstitutionViewSet, basename='institution')
router.register(r'institution-types', InstitutionTypeViewSet, basename='institution_type')
router.register(r'subjects', SubjectViewSet, basename='subjects')
router.register(r'classroom-tutors', ClassroomTutorViewSet, basename='classroom_tutors')
router.register(r'classroom-students', ClassroomStudentViewSet, basename='classroom_students')
router.register(r'classroom-examinations', ClassroomExaminationViewSet, basename='classroom_examinations')
router.register(r'classroom-attachments', ClassroomAttachmentViewSet, basename='classroom_attachments')
router.register(r'terms-and-conditions', ClassroomTermsAndConditionsViewSet, basename='classroom_terms_and_condition')
router.register(r'examination-types', ExaminationTypeViewSet, basename='examination-type')
router.register(r'assignments', AssignmentViewSet, basename = 'assignments')



urlpatterns = [
    path('', include(router.urls)),
    path('student-assignment/', StudentAssignmentCreateUpdateView.as_view(), name='assignment-submit'),
    path('student-assignment/<int:pk>/', StudentAssignmentDetailView.as_view(), name='assignment-detail'),
    path('all-submissions/', AllStudentAssignmentsView.as_view(), name='all-assignments'),

]