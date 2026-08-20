from django.urls import path, include
from drf_yasg import openapi
from rest_framework.routers import DefaultRouter
from .views import (
    AdminViewSet,
    CustomUserViewSet,
    InstitutionOwnerViewSet,
    LoginViewSet,
    ModeratorViewSet,
    RegisterViewSet,
    SocialLoginView,
    StudentViewSet,
    TeacherViewSet,
    CounselorViewSet,
    AdministratorViewSet,
    LibrarianViewSet,
    ITStaffViewSet,
    AlumniViewSet,
    GuestLecturerViewSet,
    MentorViewSet,
    ResearchPartnerViewSet,
    GovernmentAgencyViewSet,
    TutorViewSet,
    UserTypeViewSet,
    ProfileView,
    AnalyticsOverviewView,
    LogoutView,
)

router = DefaultRouter()
router.register(r'custom-users', CustomUserViewSet, basename='custom-users')
router.register(r'admins', AdminViewSet, basename='admins')
router.register(r'students', StudentViewSet, basename='students')
router.register(r'institution-owners', InstitutionOwnerViewSet, basename='institution-owners')
router.register(r'tutors', TutorViewSet, basename='tutors')
router.register(r'moderators', ModeratorViewSet, basename='moderators')
router.register(r'teachers', TeacherViewSet)
router.register(r'counselors', CounselorViewSet)
router.register(r'administrators', AdministratorViewSet)
router.register(r'librarians', LibrarianViewSet)
router.register(r'it_staff', ITStaffViewSet)
router.register(r'alumni', AlumniViewSet)
router.register(r'guest_lecturers', GuestLecturerViewSet)
router.register(r'mentors', MentorViewSet)
router.register(r'research_partners', ResearchPartnerViewSet)
router.register(r'government_agencies', GovernmentAgencyViewSet)
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'login', LoginViewSet, basename='login')
router.register(r'users', CustomUserViewSet)
router.register(r'user-types', UserTypeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('social-login/', SocialLoginView.as_view()),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('analytics/overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
]