from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

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


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer
    lookup_field = 'custom_id'


    def get_queryset(self):
        queryset = Classroom.objects.all()
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
        print("Data received:", data)  # Optional debug line

        tags_data = data.pop('tag', [])  # Get and remove 'tag' list from request

        # First: Process and create/get all Tag instances
        tag_instances = []
        for tag_name in tags_data:
            print(tag_name)
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tag_instances.append(tag)

        # Second: Now, put the tag IDs back into the payload for the serializer
        data['tag'] = [tag.id for tag in tag_instances]

        # Third: Pass everything to the serializer
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)




class ClassroomTutorViewSet(viewsets.ModelViewSet):
    queryset = ClassroomTutor.objects.all()
    serializer_class = ClassroomTutorSerializer

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

    def get_queryset(self):
        queryset = ClassroomStudent.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset


# class ExaminationTypeViewSet(viewsets.ModelViewSet):
#     queryset = ExaminationType.objects.all()
#     serializer_class = ExaminationTypeSerializer


class ClassroomExaminationViewSet(viewsets.ModelViewSet):
    queryset = ClassroomExamination.objects.all()
    serializer_class = ClassroomExaminationSerializer

    def get_queryset(self):
        queryset = ClassroomExamination.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset


class ClassroomAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ClassroomAttachment.objects.all()
    serializer_class = ClassroomAttachmentSerializer

    def get_queryset(self):
        queryset = ClassroomAttachment.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset


class ClassroomTermsAndConditionsViewSet(viewsets.ModelViewSet):
    queryset = ClassroomTermsAndConditions.objects.all()
    serializer_class = ClassroomTermsAndConditionsSerializer
