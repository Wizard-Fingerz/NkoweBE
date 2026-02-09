from rest_framework import serializers

from classroom_app.institution.models import Institution, InstitutionType, JobVacancy
from account.models import CustomUser, Student, Tutor, Teacher, Counselor, Administrator, Librarian, ITStaff, GuestLecturer, Mentor, ResearchPartner



class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = "__all__"
        
class InstitutionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionType
        fields = "__all__"

class JobVacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobVacancy
        fields = "__all__"

class ReferenceSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    relationship = serializers.CharField(max_length=100)

class StudentEnrollmentSerializer(serializers.Serializer):
    # User fields
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False) # Optional, can invoke default

    # Student fields
    date_of_birth = serializers.DateField(required=False)
    state = serializers.CharField(max_length=255, required=False)
    country = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(required=False)
    grade_level = serializers.ChoiceField(choices=[
        ('Elementary', 'Elementary'),
        ('Middle School', 'Middle School'),
        ('High School', 'High School'),
        ('College', 'College'),
    ])
    
    # Parent fields (Optional for now, but good to have)
    parent_email = serializers.EmailField(required=False)

    def create(self, validated_data):
        # Implementation will be handled in the View to avoid complex logic here if possible, 
        # or we can put it here. Let's put validation here and creation logic in view or here.
        # For now, just validating structure.
        return validated_data

class StaffEnrollmentSerializer(serializers.Serializer):
    ROLE_CHOICES = [
        ('tutor', 'Tutor'),
        ('teacher', 'Teacher'),
        ('counselor', 'Counselor'),
        ('administrator', 'Administrator'),
        ('librarian', 'Librarian'),
        ('itstaff', 'IT Staff'),
        ('guestlecturer', 'Guest Lecturer'),
        ('mentor', 'Mentor'),
        ('researchpartner', 'Research Partner'),
    ]

    # User fields
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False)

    # Common Staff fields
    role = serializers.ChoiceField(choices=ROLE_CHOICES)
    date_of_birth = serializers.DateField(required=False)
    state = serializers.CharField(max_length=255, required=False)
    country = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(required=False)
    qualification = serializers.CharField(max_length=255, required=False)
    experience = serializers.CharField(required=False)
    
    # Tutor specific
    rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    availability = serializers.CharField(required=False)
    
    def create(self, validated_data):
        return validated_data
        