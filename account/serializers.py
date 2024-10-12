from rest_framework import serializers
from .models import (
    Teacher,
    Counselor,
    Administrator,
    Librarian,
    ITStaff,
    Alumni,
    GuestLecturer,
    Mentor,
    ResearchPartner,
    GovernmentAgency,
    CustomUser, Admin, InstitutionalOwner, Student, Tutor, Moderator,
    UserType
 )

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"
        

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = "__all__"


class DetailedStudentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    class Meta:
        model = Student
        fields = "__all__"

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"


class InstitutionOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionalOwner
        fields = "__all__"

class TutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tutor
        fields = "__all__"

class ModeratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moderator
        fields = "__all__"

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

class CounselorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counselor
        fields = '__all__'

class AdministratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = '__all__'

class LibrarianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Librarian
        fields = '__all__'

class ITStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = ITStaff
        fields = '__all__'

class AlumniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumni
        fields = '__all__'

class GuestLecturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestLecturer
        fields = '__all__'

class MentorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentor
        fields = '__all__'

class ResearchPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchPartner
        fields = '__all__'

class GovernmentAgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentAgency
        fields = '__all__'

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser 
        fields = ('username', 'email', 'password', 'user_type')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        try:
            user = CustomUser.objects.create_user(**validated_data)
            return user
        except Exception as e:
            print(f"Error creating user: {e}")
            raise


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()