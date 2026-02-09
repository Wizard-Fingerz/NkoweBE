from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from account.models import CustomUser, InstitutionalOwner
from classroom_app.institution.models import Institution, JobVacancy
from classroom_app.definitions.insitution_types.models import InstitutionType
from account.models import Teacher, Student

class JobVacancyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='admin', email='admin@example.com', password='password123')
        self.institution_type = InstitutionType.objects.create(name="School")
        self.institution = Institution.objects.create(name="Test Institution", institution_type=self.institution_type, email="test@test.com")
        self.owner = InstitutionalOwner.objects.create(user=self.user, institution=self.institution, email='admin@example.com')
        self.client.force_authenticate(user=self.user)
        self.vacancy_url = reverse('job-vacancies-list')

    def test_create_vacancy(self):
        data = {
            "institution": self.institution.id,
            "title": "Math Teacher",
            "description": "Teach math",
            "requirements": "Degree in Math",
            "job_type": "Full-time",
            "deadline": "2024-12-31T23:59:59Z"
        }
        response = self.client.post(self.vacancy_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobVacancy.objects.count(), 1)
        self.assertEqual(JobVacancy.objects.get().title, "Math Teacher")

    def test_list_vacancies(self):
        JobVacancy.objects.create(
            institution=self.institution,
            title="Science Teacher",
            description="Teach Science",
            requirements="Degree in Science",
            job_type="Full-time",
            deadline="2024-12-31T23:59:59Z"
        )
        response = self.client.get(self.vacancy_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class EnrollmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='admin', email='admin@example.com', password='password123')
        self.institution_type = InstitutionType.objects.create(name="School")
        self.institution = Institution.objects.create(name="Test Institution", institution_type=self.institution_type, email="test@test.com")
        self.owner = InstitutionalOwner.objects.create(user=self.user, institution=self.institution, email='admin@example.com')
        self.client.force_authenticate(user=self.user)
        # Using basename 'institution-enrollment' -> detail route enroll-student -> institution-enrollment-enroll-student
        self.enroll_student_url = reverse('institution-enrollment-enroll-student', args=[self.institution.id])
        self.enroll_staff_url = reverse('institution-enrollment-enroll-staff', args=[self.institution.id])

    def test_enroll_student(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "password123",
            "date_of_birth": "2010-01-01",
            "grade_level": "High School"
        }
        response = self.client.post(self.enroll_student_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email="john.doe@example.com").exists())
        # Student model check - access via reverse relation on Institution if possible or direct query
        # Student has m2m to Institution.
        student_user = CustomUser.objects.get(email="john.doe@example.com")
        self.assertTrue(Student.objects.filter(user=student_user).exists())
        student = Student.objects.get(user=student_user)
        self.assertTrue(student.institutions.filter(pk=self.institution.pk).exists())

    def test_enroll_staff(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "password": "password123",
            "role": "teacher",
            "qualification": "PhD"
        }
        response = self.client.post(self.enroll_staff_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email="jane.smith@example.com").exists())
        teacher_user = CustomUser.objects.get(email="jane.smith@example.com")
        self.assertTrue(Teacher.objects.filter(user=teacher_user).exists())
        teacher = Teacher.objects.get(user=teacher_user)
        self.assertTrue(teacher.institutions.filter(pk=self.institution.pk).exists())
