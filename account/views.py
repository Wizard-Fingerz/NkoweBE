from django.db import transaction
from .serializers import (
    DetailedStudentSerializer,
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
from rest_framework.permissions import IsAuthenticated
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


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class AdminViewSet(viewsets.ModelViewSet):
    queryset = Admin.objects.all()
    serializer_class = AdminSerializer


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
        user.user_type = UserType.STUDENT
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
    queryset = InstitutionalOwner.objects.all()
    serializer_class = InstitutionOwnerSerializer


class TutorViewSet(viewsets.ModelViewSet):
    queryset = Tutor.objects.all()
    serializer_class = TutorSerializer


class ModeratorViewSet(viewsets.ModelViewSet):
    queryset = Moderator.objects.all()
    serializer_class = ModeratorSerializer

# views.py


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user.user_type == 'teacher':
                queryset = queryset.filter(user=user)
        return queryset


class CounselorViewSet(viewsets.ModelViewSet):
    queryset = Counselor.objects.all()
    serializer_class = CounselorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user.user_type == 'counselor':
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
            if user.user_type == 'administrator':
                queryset = queryset.filter(user=user)
        return queryset


class LibrarianViewSet(viewsets.ModelViewSet):
    queryset = Librarian.objects.all()
    serializer_class = LibrarianSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user
        if user.is_authenticated:
            if user.user_type == 'librarian':
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
            if user.user_type == 'it_staff':
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
            if user.user_type == 'alumni':
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
            if user.user_type == 'guest_lecturer':
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
            if user.user_type == 'mentor':
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
            if user.user_type == 'research_partner':
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
            if user.user_type == 'government_agency':
                queryset = queryset.filter(user=user)
        return queryset


class RegisterViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.get(user=user)
            data = serializer.data
            data['token'] = token.key
            
            data['user_id'] = user.id
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = LoginSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=200)
            else:
                return Response({'message': 'Invalid username or password'}, status=401)
        else:
            return Response(serializer.errors, status=400)


class SocialLoginView(APIView):
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
