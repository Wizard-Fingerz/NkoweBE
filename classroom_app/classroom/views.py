from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import Classroom, ClassroomTermsAndConditions, ClassroomTutor, ClassroomStudent, ExaminationType, ClassroomExamination, ClassroomAttachment
from .serializers import ClassroomSerializer, ClassroomTermsAndConditionsSerializer, ClassroomTutorSerializer, ClassroomStudentSerializer, ExaminationTypeSerializer, ClassroomExaminationSerializer, ClassroomAttachmentSerializer

class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer

    def get_queryset(self):
        queryset = Classroom.objects.all()
        institution_id = self.request.query_params.get('institution_id')
        subject_id = self.request.query_params.get('subject_id')
        if institution_id is not None:
            queryset = queryset.filter(institution_id=institution_id)
        if subject_id is not None:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset

class ClassroomTutorViewSet(viewsets.ModelViewSet):
    queryset = ClassroomTutor.objects.all()
    serializer_class = ClassroomTutorSerializer

    def get_queryset(self):
        queryset = ClassroomTutor.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset

class ClassroomStudentViewSet(viewsets.ModelViewSet):
    queryset = ClassroomStudent.objects.all()
    serializer_class = ClassroomStudentSerializer

    def get_queryset(self):
        queryset = ClassroomStudent.objects.all()
        classroom_id = self.request.query_params.get('classroom_id')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset

class ExaminationTypeViewSet(viewsets.ModelViewSet):
    queryset = ExaminationType.objects.all()
    serializer_class = ExaminationTypeSerializer

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