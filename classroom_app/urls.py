from django.urls import path, include
from rest_framework import routers

from classroom_app.classroom.views import ClassroomTermsAndConditionsViewSet
from classroom_app.institution.views import InstitutionViewSet
from .views import ClassroomViewSet, ClassroomTutorViewSet, ClassroomStudentViewSet, ExaminationTypeViewSet, ClassroomExaminationViewSet, ClassroomAttachmentViewSet

router = routers.DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classrooms')
router.register(r'institution', InstitutionViewSet, basename='institution')
router.register(r'classroom_tutors', ClassroomTutorViewSet, basename='classroom_tutors')
router.register(r'classroom_students', ClassroomStudentViewSet, basename='classroom_students')
router.register(r'examination_types', ExaminationTypeViewSet, basename='examination_types')
router.register(r'classroom_examinations', ClassroomExaminationViewSet, basename='classroom_examinations')
router.register(r'classroom_attachments', ClassroomAttachmentViewSet, basename='classroom_attachments')
router.register(r'terms-and-conditions', ClassroomTermsAndConditionsViewSet, basename='classroom_terms_and_condition')

urlpatterns = [
    path('', include(router.urls)),
]