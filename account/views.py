from django.db import transaction
from .serializers import (
    DetailedStudentSerializer,
    DetailedTeacherSerializer,
    DetailedAdministratorSerializer,
    LoginSerializer,
    RegisterSerializer,
    TeacherSerializer,
    CounselorSerializer,
    AdministratorSerializer,
    LibrarianSerializer,
    ITStaffSerializer,
    AlumniSerializer,
    GuestLecturerSerializer,
    MentorSerializer,
    ResearchPartnerSerializer,
    GovernmentAgencySerializer,
    CustomUserSerializer, AdminSerializer, StudentSerializer, InstitutionOwnerSerializer, TutorSerializer, ModeratorSerializer,
    UserTypeSerializer,
)
from .models import (
    Teacher,
    Counselor,
    Administrator,
    Librarian,
    ITStaff,
    Alumni,
    GuestLecturer,
    Mentor,
    ResearchPartner, CustomUser, Admin, Student, InstitutionalOwner, Tutor, Moderator,
    GovernmentAgency,
    UserType,
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from django.db import IntegrityError
from rest_framework.decorators import action
from classroom_app.classroom.models import Classroom, ClassroomStudent
from classroom_app.assignment.models import Assignment, StudentAssignment


def user_has_type(user, type_name):
    """
    Safely check a CustomUser's role.

    `user_type` is a ForeignKey to UserType, not a string — comparing it
    directly to a string literal (e.g. `user.user_type == 'teacher'`) is
    always False in both directions and was silently disabling every
    "only see your own records" filter in this file, while simultaneously
    blocking legitimate teachers/admins from actions gated the same way.
    Use this helper everywhere a role check is needed instead.
    """
    ut = getattr(user, 'user_type', None)
    return bool(ut and ut.name.lower() == type_name.lower())


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Full user-account records. This previously had NO permission_classes at
    all, which — combined with no project-wide DEFAULT_PERMISSION_CLASSES —
    meant anyone on the internet could list, create, update, or delete any
    user account with no authentication. Restricted to authenticated users,
    and non-staff users are further restricted to their own record.
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(pk=user.pk)


class AdminViewSet(viewsets.ModelViewSet):
    # Was fully open (no permission_classes). Admin-profile management is
    # restricted to Django staff/superusers.
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer
    permission_classes = [IsAdminUser]


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DetailedStudentSerializer
        else:
            return StudentSerializer
        

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        user = request.user
        user.first_name = request.data.get('first_name')
        user.last_name = request.data.get('last_name')
        user.user_type = UserType.objects.get(name = 'Student')
        user.save()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='me', url_name='me')
    def get_current_user(self, request):
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = Student.objects.create(user=request.user)
        
        serializer = self.get_serializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)  
        
class InstitutionOwnerViewSet(viewsets.ModelViewSet):
    # Was fully open (no permission_classes).
    queryset = InstitutionalOwner.objects.all()
    serializer_class = InstitutionOwnerSerializer
    permission_classes = [IsAuthenticated]


class TutorViewSet(viewsets.ModelViewSet):
    # Was fully open (no permission_classes).
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer
    permission_classes = [IsAuthenticated]


class ModeratorViewSet(viewsets.ModelViewSet):
    # Was fully open (no permission_classes). Moderator-profile management is
    # restricted to Django staff/superusers, same as AdminViewSet.
    queryset = Moderator.objects.all()
    serializer_class = ModeratorSerializer
    permission_classes = [IsAdminUser]

# views.py


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'teacher'):
                queryset = queryset.filter(user=user)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DetailedTeacherSerializer
        else:
            return TeacherSerializer
    
    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        user = request.user
        user.first_name = request.data.get('first_name')
        user.last_name = request.data.get('last_name')
        user.user_type = UserType.objects.get(name = 'Teacher')
        user.save()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='me', url_name='me')
    def get_current_user(self, request):
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            teacher = Teacher.objects.create(user=request.user)
        
        serializer = self.get_serializer(teacher)
        return Response(serializer.data, status=status.HTTP_200_OK)  
     

class CounselorViewSet(viewsets.ModelViewSet):
    queryset = Counselor.objects.all()
    serializer_class = CounselorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'counselor'):
                queryset = queryset.filter(user=user)
        return queryset


class AdministratorViewSet(viewsets.ModelViewSet):
    queryset = Administrator.objects.all()
    serializer_class = AdministratorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'administrator'):
                queryset = queryset.filter(user=user)
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create an Administrator profile for the currently authenticated user.
        The `user` OneToOne field is automatically set to `request.user`.
        """
        # Force the profile to be linked to the logged-in user
        data = request.data.copy()
        data['user'] = request.user.id

        # Optionally keep CustomUser in sync with provided details
        user = request.user
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        # Ensure the user_type is set to "Administrator"
        try:
            admin_type = UserType.objects.get(name='Administrator')
            user.user_type = admin_type
        except UserType.DoesNotExist:
            pass

        user.save()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class LibrarianViewSet(viewsets.ModelViewSet):
    queryset = Librarian.objects.all()
    serializer_class = LibrarianSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'librarian'):
                queryset = queryset.filter(user=user)
        return queryset


class ITStaffViewSet(viewsets.ModelViewSet):
    queryset = ITStaff.objects.all()
    serializer_class = ITStaffSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'it_staff'):
                queryset = queryset.filter(user=user)
        return queryset


class AlumniViewSet(viewsets.ModelViewSet):
    queryset = Alumni.objects.all()
    serializer_class = AlumniSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'alumni'):
                queryset = queryset.filter(user=user)
        return queryset


class GuestLecturerViewSet(viewsets.ModelViewSet):
    queryset = GuestLecturer.objects.all()
    serializer_class = GuestLecturerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'guest_lecturer'):
                queryset = queryset.filter(user=user)
        return queryset


class MentorViewSet(viewsets.ModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'mentor'):
                queryset = queryset.filter(user=user)
        return queryset


class ResearchPartnerViewSet(viewsets.ModelViewSet):
    queryset = ResearchPartner.objects.all()
    serializer_class = ResearchPartnerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'research_partner'):
                queryset = queryset.filter(user=user)
        return queryset


class GovernmentAgencyViewSet(viewsets.ModelViewSet):
    queryset = GovernmentAgency.objects.all()
    serializer_class = GovernmentAgencySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user_has_type(user, 'government_agency'):
                queryset = queryset.filter(user=user)
        return queryset


class RegisterViewSet(viewsets.ModelViewSet):
    # Must stay public: this is how new accounts are created. Explicit now
    # that the project-wide default is IsAuthenticated — without this, no
    # one could register at all.
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        # Autogenerate username as lowercase "lastname.firstname" (no spaces, fallback if missing fields)
        if last_name and first_name:
            base_username = f"{last_name}.{first_name}".replace(' ', '').lower()
        elif first_name:
            base_username = first_name.replace(' ', '').lower()
        elif last_name:
            base_username = last_name.replace(' ', '').lower()
        else:
            base_username = 'user'

        # Ensure the username is unique
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        data['username'] = username

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.get(user=user)
            resp_data = serializer.data
            resp_data['token'] = token.key
            resp_data['user_id'] = user.id
            return Response(resp_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginViewSet(viewsets.ModelViewSet):
    # Must stay public: this is how users authenticate in the first place.
    queryset = CustomUser.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username_or_email = serializer.validated_data['username_or_email']
        password = serializer.validated_data['password']

        user = authenticate(
            request,
            username=username_or_email,
            password=password
        )

        if not user:
            return Response(
                {'message': 'Invalid username/email or password'},
                status=401
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'user_type': user.user_type.name,
            }
        }, status=200)



class SocialLoginView(APIView):
    # Must stay public: this is a login entry point.
    permission_classes = [AllowAny]

    def post(self, request):
        provider = request.data.get('provider')
        if provider == 'google':
            adapter = GoogleOAuth2Adapter(request)
            token = adapter.get_access_token(request.data.get('code'))
            user = adapter.get_user(token)
            # Create a new user or login existing user
            return Response({'token': user.auth_token.key}, status=200)
        elif provider == 'twitter':
            adapter = TwitterOAuthAdapter(request)
            token = adapter.get_access_token(request.data.get(
                'oauth_token'), request.data.get('oauth_verifier'))
            user = adapter.get_user(token)
            # Create a new user or login existing user
            return Response({'token': user.auth_token.key}, status=200)
        elif provider == 'facebook':
            adapter = FacebookOAuth2Adapter(request)
            token = adapter.get_access_token(request.data.get('code'))
            user = adapter.get_user(token)
            # Create a new user or login existing user
            return Response({'token': user.auth_token.key}, status=200)
        else:
            return Response({'error': 'Invalid provider'}, status=400)


class UserTypeViewSet(viewsets.ModelViewSet):
    # The list of role types (student/teacher/etc.) is needed on the public
    # registration form, so reads stay open; writes require authentication.
    # Mirrors the pattern already used correctly elsewhere in this codebase
    # (SubjectViewSet, InstitutionTypeViewSet, ExaminationTypeViewSet).
    queryset = UserType.objects.filter(is_active=True)
    serializer_class = UserTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return UserType.objects.filter(is_active=True, is_deleted=False)


class LogoutView(APIView):
    """
    Deletes the requesting user's auth token, invalidating it for future
    requests. The frontend's AuthApiService.logout() already POSTs to
    /logout/; previously no such route existed, so it silently 404'd and
    the token stayed valid forever after "logging out".
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user
        user_type = getattr(user, 'user_type', None)
        profile = None
        serializer = None

        if user_type is None:
            return Response({'detail': 'User type not set.'}, status=status.HTTP_400_BAD_REQUEST)

        if str(user_type).lower() == 'student':
            from .models import Student
            from .serializers import DetailedStudentSerializer
            try:
                profile = Student.objects.get(user=user)
                serializer = DetailedStudentSerializer(profile)
            except Student.DoesNotExist:
                return Response({'detail': 'Student profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        elif str(user_type).lower() == 'teacher':
            from .models import Teacher
            from .serializers import DetailedTeacherSerializer
            try:
                profile = Teacher.objects.get(user=user)
                serializer = DetailedTeacherSerializer(profile)
            except Teacher.DoesNotExist:
                return Response({'detail': 'Teacher profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        elif str(user_type).lower() == 'administrator':
            try:
                profile = Administrator.objects.get(user=user)
                serializer = DetailedAdministratorSerializer(profile)
            except Administrator.DoesNotExist:
                return Response({'detail': 'Administrator profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Add more user types as needed
        # elif str(user_type).lower() == 'counselor':
        #     ...

        else:
            return Response({'detail': f'Profile for user type {user_type} not implemented.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user
        user_type = getattr(user.user_type, 'name', '').lower() if user.user_type else ''
        data = {}

        if user_type == 'admin':
            data = {
                'totalUsers': CustomUser.objects.count(),
                'totalTeachers': Teacher.objects.count(),
                'totalStudents': Student.objects.count(),
                'totalClassrooms': Classroom.objects.count(),
                'totalAssignments': Assignment.objects.count(),
                'assignmentsSubmitted': StudentAssignment.objects.filter(status='completed').count(),
                # Add more as needed
            }
        elif user_type == 'teacher':
            teacher = Teacher.objects.filter(user=user).first()
            data = {
                'totalClassesTaught': Classroom.objects.filter(classroomtutor__tutor__user=user).count(),
                'totalStudents': Student.objects.count(),  # Optionally filter by teacher's classes
                'assignmentsGiven': Assignment.objects.filter(created_by__tutor=teacher).count() if teacher else 0,
                'examsCreated': 0,  # Placeholder, add logic if you have exams
            }
        elif user_type == 'student':
            student = Student.objects.filter(user=user).first()
            # Get the ClassroomStudent instance(s) for this student
            classroom_students = ClassroomStudent.objects.filter(student=student) if student else []
            total_courses_enrolled = classroom_students.count() if student else 0

            # Get all StudentAssignment for this student
            student_assignments = StudentAssignment.objects.filter(student__student=student) if student else []
            # Calculate highest score (if scores are stored in StudentAssignment or related models)
            # For now, let's assume Assignment has total_score, but StudentAssignment does not store obtained score
            # If you store obtained score elsewhere, update this logic accordingly
            highest_score = None
            if student_assignments:
                # If you have a field for obtained score, use it. Otherwise, this is a placeholder.
                # Example: max(sa.obtained_score for sa in student_assignments if sa.obtained_score is not None)
                pass

            data = {
                'totalClassrooms': Classroom.objects.filter(classroomstudent__student=student).count() if student else 0,
                'totalAssignments': StudentAssignment.objects.filter(student__student=student).count() if student else 0,
                'assignmentsCompleted': StudentAssignment.objects.filter(student__student=student, status='completed').count() if student else 0,
                'totalCoursesEnrolled': total_courses_enrolled,
                'highestScore': highest_score,
                'totalNotes': 0,  # Not implemented
                'totalNotebooks': 0,  # Not implemented
                'totalHighlights': 0,  # Not implemented
            }
        else:
            data = {'message': 'Analytics not available for this user type.'}

        return Response(data)
