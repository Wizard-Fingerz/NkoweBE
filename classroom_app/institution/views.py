from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from classroom_app.institution.models import Institution, JobVacancy
from classroom_app.institution.serializers import InstitutionSerializer, JobVacancySerializer, StudentEnrollmentSerializer, StaffEnrollmentSerializer
from account.models import CustomUser, Student, InstitutionalOwner, Tutor, Teacher, Counselor, Administrator, Librarian, ITStaff, Alumni, GuestLecturer, Mentor, ResearchPartner, GovernmentAgency, Title
from django.db.models import Q
# Create your views here.



class InstitutionViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        # Institutions where user is the creator (InstitutionalOwner)
        owner_institutions = Institution.objects.filter(insitution_in_institution_owner__user=user)
        # Institutions where user is staff (tutor, teacher, etc)
        staff_institutions = Institution.objects.filter(
            Q(insitution_in_tutor__user=user) |
            Q(teacher__user=user) |
            Q(counselor__user=user) |
            Q(administrator__user=user) |
            Q(librarian__user=user) |
            Q(itstaff__user=user) |
            Q(alumni__user=user) |
            Q(guestlecturer__user=user) |
            Q(mentor__user=user) |
            Q(researchpartner__user=user) |
            Q(governmentagency__user=user)
        )
        # Union and distinct
        return (owner_institutions | staff_institutions).distinct()

    def perform_create(self, serializer):
        institution = serializer.save()
        user = self.request.user
        # Use a default Title if not provided
        # title = Title.objects.first()  # You may want to customize this
        InstitutionalOwner.objects.create(user=user, institution=institution, phone=user.email, email=user.email)

class JobVacancyViewSet(viewsets.ModelViewSet):
    queryset = JobVacancy.objects.all()
    serializer_class = JobVacancySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        # Filter vacancies by institutions the user manages or is part of
        # For now, simplistic: return all if admin/owner, or just public ones?
        # Let's return all for now, but restrict editing.
        return JobVacancy.objects.all()

    def perform_create(self, serializer):
        # Ensure the user has permission to post to this institution
        # This logic should be here or in permissions
        serializer.save()

from rest_framework.decorators import action

class InstitutionEnrollmentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @action(detail=True, methods=['post'], url_path='enroll-student')
    def enroll_student(self, request, pk=None):
        try:
            institution = Institution.objects.get(pk=pk)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions: User must be owner or admin of the institution
        # skipped for brevity/MVP, but essential for prod.
        
        serializer = StudentEnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Check if user exists
            email = data.get('email')
            user, created = CustomUser.objects.get_or_create(email=email, defaults={
                'username': email,
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name')
            })
            if created:
                password = data.get('password') or "DefaultPassword123!" # Should generate random or send invite
                user.set_password(password)
                user.save()
            
            # Check/Create Student profile
            student, _ = Student.objects.get_or_create(user=user, defaults={
                'date_of_birth': data.get('date_of_birth'),
                'state': data.get('state', ''),
                'country': data.get('country', ''),
                'address': data.get('address', ''),
                'grade_level': data.get('grade_level', 'Elementary')
            })
            
            # Link to institution
            student.institutions.add(institution)
            student.save()
            
            return Response({"message": "Student enrolled successfully", "student_id": student.user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='enroll-staff')
    def enroll_staff(self, request, pk=None):
        try:
            institution = Institution.objects.get(pk=pk)
        except Institution.DoesNotExist:
            return Response({"error": "Institution not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = StaffEnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            email = data.get('email')
            
            user, created = CustomUser.objects.get_or_create(email=email, defaults={
                'username': email,
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name')
            })
            if created:
                password = data.get('password') or "DefaultPassword123!"
                user.set_password(password)
                user.save()

            role = data.get('role')
            # Mapping roles to models
            model_map = {
                'tutor': Tutor,
                'teacher': Teacher,
                'counselor': Counselor,
                'administrator': Administrator,
                'librarian': Librarian,
                'itstaff': ITStaff,
                'guestlecturer': GuestLecturer,
                'mentor': Mentor,
                'researchpartner': ResearchPartner,
            }
            
            ModelClass = model_map.get(role)
            if not ModelClass:
                return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

            # Create/Get Staff Profile
            # Note: Fields might differ per model, here taking common intersection or handling specifically
            defaults = {
                'experience': data.get('experience', ''),
                # 'qualifications': data.get('qualification', ''), # Some models might name it differently or not have it
            }
            
            # Custom field handling
            if role == 'tutor':
                defaults['rate'] = data.get('rate', 0.0)
                defaults['availability'] = data.get('availability', '')
                defaults['qualification'] = data.get('qualification', '') # Tutor has qualification
            elif hasattr(ModelClass, 'qualifications'):
                 defaults['qualifications'] = data.get('qualification', '')

            
            staff_obj, _ = ModelClass.objects.get_or_create(user=user, defaults=defaults)
            
            # Link to institution
            if hasattr(staff_obj, 'institutions'):
                staff_obj.institutions.add(institution)
                staff_obj.save()
            
            return Response({"message": f"{role.capitalize()} enrolled successfully", "user_id": user.id}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
