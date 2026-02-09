from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from account.models import CustomUser, InstitutionalOwner, Teacher, Student
from classroom_app.institution.models import Institution
from classroom_app.definitions.insitution_types.models import InstitutionType
from classroom_app.classroom.models import Classroom, ClassroomStudent, ClassroomTutor
# import your Serializers if needed for mock data validation

class ClassroomManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create Admin/Owner
        self.admin_user = CustomUser.objects.create_user(username='admin', email='admin@example.com', password='password123')
        self.institution_type = InstitutionType.objects.create(name="School")
        self.institution = Institution.objects.create(name="Test Institution", institution_type=self.institution_type, email="test@test.com")
        self.owner = InstitutionalOwner.objects.create(user=self.admin_user, institution=self.institution, email='admin@example.com')
        
        # Create Teacher
        self.teacher_user = CustomUser.objects.create_user(username='teacher', email='teacher@example.com', password='password123')
        self.teacher = Teacher.objects.create(user=self.teacher_user, qualification="PhD")
        self.teacher.institutions.add(self.institution)

        # Create Student
        self.student_user = CustomUser.objects.create_user(username='student', email='student@example.com', password='password123')
        self.student = Student.objects.create(user=self.student_user, grade_level="10")
        self.student.institutions.add(self.institution)

        self.classroom_url = reverse('classroom-list') # key from router
        
    def test_create_classroom_by_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "name": "Math 101",
            "capacity": 30,
            "description": "Intro to Math",
            "institution": self.institution.id
        }
        response = self.client.post(self.classroom_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Classroom.objects.count(), 1)
        self.assertEqual(Classroom.objects.get().created_by, self.admin_user)

    def test_add_student_to_classroom(self):
        # First create a classroom
        self.client.force_authenticate(user=self.admin_user)
        classroom = Classroom.objects.create(
            name="Science 101", 
            capacity=20, 
            institution=self.institution,
            created_by=self.admin_user
        )
        
        # Add student
        url = reverse('classroom-student-list')
        data = {
            "classroom": classroom.id,
            "student": self.student_user.email # We updated viewset to accept email or ID logic in create()
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ClassroomStudent.objects.filter(classroom=classroom, student=self.student).exists())

    def test_add_tutor_to_classroom(self):
        # First create a classroom
        self.client.force_authenticate(user=self.admin_user)
        classroom = Classroom.objects.create(
            name="English 101", 
            capacity=20, 
            institution=self.institution,
            created_by=self.admin_user
        )
        
        # Add tutor
        url = reverse('classroom-tutor-list')
        data = {
            "classroom": classroom.id,
            "tutor": self.teacher_user.email,
            "role": "TEACHER"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ClassroomTutor.objects.filter(classroom=classroom, tutor=self.teacher_user).exists())
