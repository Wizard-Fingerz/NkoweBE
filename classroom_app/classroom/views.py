from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from account.models import CustomUser, Tutor
from .models import Classroom, ClassroomTermsAndConditions, ClassroomTutor, ClassroomStudent, ExaminationType, ClassroomExamination, ClassroomAttachment, Tag
from .serializers import ClassroomSerializer, ClassroomTermsAndConditionsSerializer, ClassroomTutorSerializer, ClassroomStudentSerializer, DetailedClassroomSerializer, ExaminationTypeSerializer, ClassroomExaminationSerializer, ClassroomAttachmentSerializer


from rest_framework import viewsets, pagination


class CustomPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'num_pages': self.page.paginator.num_pages,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'results': data
        })


from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    lookup_field = 'custom_id'
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Classroom.objects.all()
        
        # If user is student, filter by enrollment (using ClassroomStudent)
        if hasattr(user, 'student'): # Assuming relation or check
            # This is complex if we don't have direct relation easily accessible here without more queries
            # For now, let's trust the FE filters or implement robust filtering later.
            pass

        institution_id = self.request.query_params.get('institution_id')
        subject_id = self.request.query_params.get('subject_id')
        if institution_id is not None:
            queryset = queryset.filter(institution_id=institution_id)
        if subject_id is not None:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return DetailedClassroomSerializer
        return ClassroomSerializer
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # Auto-assign institution if not provided, based on user's institution
        # This assumes user is linked to an institution (Owner/Staff)
        if 'institution' not in data:
            # Logic to find user's institution. 
            # For MVP, we might expect it in payload or pick first one.
            # user.institution_owner.first().institution.id ??
            pass

        tags_data = data.pop('tag', []) 
        tag_instances = []
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tag_instances.append(tag)
        data['tag'] = [tag.id for tag in tag_instances]

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)



    @action(detail=True, methods=['get'])
    def attachments(self, request, custom_id=None):
        classroom = self.get_object()
        attachments = classroom.classroomattachment_set.all()
        data = ClassroomAttachmentSerializer(attachments, many=True).data
        return Response(data)

    @action(detail=True, methods=['get'])
    def tutors(self, request, custom_id=None):
        classroom = self.get_object()
        classroom_tutors = classroom.classroomtutor_set.all()
        data = ClassroomTutorSerializer(classroom_tutors, many=True).data
        return Response(data)

    @action(detail=True, methods=['get'])
    def students(self, request, custom_id=None):
        classroom = self.get_object()
        classroom_students = classroom.classroomstudent_set.all()
        data = ClassroomStudentSerializer(classroom_students, many=True).data
        return Response(data)



class ClassroomTutorViewSet(viewsets.ModelViewSet):
    queryset = ClassroomTutor.objects.all()
    serializer_class = ClassroomTutorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ClassroomTutor.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset

    def create(self, request, *args, **kwargs):
        tutor_email = request.data.get('tutor')
        role = request.data.get('role')
        classroom_id = request.data.get('classroom')

        if not tutor_email or not role or not classroom_id:
            return Response({'detail': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=tutor_email)

            try:
                tutor_profile = Tutor.objects.get(user=user)

                # User and Tutor profile both exist
                classroom_tutor, created = ClassroomTutor.objects.get_or_create(
                    classroom_id=classroom_id,
                    tutor=user,
                    defaults={'role': role}
                )

                if not created:
                    return Response({'detail': 'This tutor is already assigned to the classroom.'}, status=status.HTTP_400_BAD_REQUEST)

                self.send_invite_notification(user, classroom_tutor)
                return Response(self.get_serializer(classroom_tutor).data, status=status.HTTP_201_CREATED)

            except Tutor.DoesNotExist:
                # User exists, but no Tutor profile
                return Response({'detail': 'User exists but has no tutor profile. Please ask them to complete their Tutor registration first.'},
                                status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            # No user at all — Send sign up invitation
            self.send_signup_invite_email(tutor_email, classroom_id, role)
            return Response({'detail': f'Invitation sent to {tutor_email} to sign up and join the class.'}, status=status.HTTP_201_CREATED)

    def send_invite_notification(self, user, classroom_tutor):
        # Example: Notify existing user to accept
        print(f"Send internal notification to {user.email} to accept tutor invitation for classroom {classroom_tutor.classroom_id}")

    def send_signup_invite_email(self, email, classroom_id, role):
        # Example: Email invitation for new user
        print(f"Send email to {email} to sign up and become a tutor for classroom {classroom_id} (Role: {role})")

class ClassroomStudentViewSet(viewsets.ModelViewSet):
    queryset = ClassroomStudent.objects.all()
    serializer_class = ClassroomStudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ClassroomStudent.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset

    def create(self, request, *args, **kwargs):
        student_email = request.data.get('student') # Expect email or ID? Let's check format. modal sends email.
        classroom_id = request.data.get('classroom')

        if not student_email or not classroom_id:
            return Response({'detail': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        # If it looks like an ID (integer), fallback to default behavior? 
        # But safest is to treat as email if string.
        
        try:
            # Check if student_email is actually an ID (int)
            if isinstance(student_email, int) or (isinstance(student_email, str) and student_email.isdigit()):
                 return super().create(request, *args, **kwargs)
            
            user = CustomUser.objects.get(email=student_email)
            try:
                student_profile = Student.objects.get(user=user)
                
                classroom_student, created = ClassroomStudent.objects.get_or_create(
                    classroom_id=classroom_id,
                    student=student_profile
                )
                
                if not created:
                    return Response({'detail': 'Student already in class.'}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response(self.get_serializer(classroom_student).data, status=status.HTTP_201_CREATED)

            except Student.DoesNotExist:
                return Response({'detail': 'User exists but is not registered as a Student.'}, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            return Response({'detail': 'Student not found with this email.'}, status=status.HTTP_404_NOT_FOUND)


# class ExaminationTypeViewSet(viewsets.ModelViewSet):
#     queryset = ExaminationType.objects.all()
#     serializer_class = ExaminationTypeSerializer


class ClassroomExaminationViewSet(viewsets.ModelViewSet):
    queryset = ClassroomExamination.objects.all()
    serializer_class = ClassroomExaminationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ClassroomExamination.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset


class ClassroomAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ClassroomAttachment.objects.all()
    serializer_class = ClassroomAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ClassroomAttachment.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset


class ClassroomTermsAndConditionsViewSet(viewsets.ModelViewSet):
    queryset = ClassroomTermsAndConditions.objects.all()
    serializer_class = ClassroomTermsAndConditionsSerializer
    permission_classes = [IsAuthenticated]
